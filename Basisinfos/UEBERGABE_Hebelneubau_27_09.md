# Übergabe an die nächste Session — Hebelneubau

**Stand 27.09.2026 abends.** Zehn Fragen, zehn Antworten.

> ⚠️⚠️ **Jede Antwort nennt den Befehl, mit dem du sie selbst prüfst.**
> Wo ich nur wiedergebe, steht ein **Vorbehalt** dabei. Meine Wiedergabe
> ist nicht die Quelle — der Befehl ist es.

> ⛔ **Dieses Blatt ersetzt die Übergabe aus der Zeit vor dem
> Hebelneubau.** Die alte handelte vom Spot-Arm und einer gemeinsamen
> Bewertung. Beides gilt nicht mehr.

---

# ⭐⭐⭐ NACHTRAG STAND 29.09.2026 — vor dem vom 28.09. lesen

| Frage | neu |
|---|---|
| **5 · Was trägt** | die **Auswahl nach dem Beitrag** ist robust (2.680, T6/T4/T5), aber **rsi allein** wählt besser aus; die Kombination bringt nichts dazu |
| **9 · Hebel** | K7 (2.679): **Markpreis** Hauptmaß, m = 0,09 vorsichtig, Fehlalarme nur über 5x · K6 (2.681): die **ATR allein** trägt die Liquidationsgefahr, die Risikokurven nicht; 5x kalibriert, 3x geordnet, 2x zu selten; H0 und J10 offen |
| **10 · Nächster Schritt** | **K5 neu abstimmen** (die Nutzervorgabe *wenn das auch nicht klappt, müssen wir wieder abstimmen* ist eingetreten) · K6 mit dem Markpreis auswerten · die Importer-Voranalyse (Buch statt Position) **im Hauptfenster** vorlegen, spätestens in Phase 2 |

```bash
python hebel_neubau.py | sed -n '/NEUESTER STAND/,/DIE NAECHSTEN/p'
```

---

# ⭐⭐⭐ NACHTRAG STAND 28.09.2026 — zuerst lesen

Die zehn Antworten unten sind vom 27.09. abends. **Seitdem geändert:**

| Frage | neu |
|---|---|
| **3/4 · Ablauf und Regelwerk** | die **Anwendungsebene K1–K7** ist abgestimmt — Wirkungskurven statt Schalter, Urteil gegen die **Phase** des Assets, Ereignis **q5** (+5 vor −5 % in 24 h), Schwelle auf kalibriertem q mit 3–5 Stufen, Hebelstufe aus der **Liquidationsgefahr**, Messbasis Binance. `Regelwerk_Hebel_Bewertung_27_09.md`, Block *Stand 28.09.* und *Pflichtablauf Fassung 28.09.* |
| **5 · Was trägt** | ✔ rsi und momentum_kurz **oberer Rand** je Asset (4 von 4 Mengen, A4 bestätigt, Altersachse gültig) · ema_abstand selbstbezogen als **Kurve** · ⭐ der **24 h alte** Wert oben in jedem Zeitraum · ⚠️ funding_markt / konten_verh_markt **unterer Rand** nur in der Suche · ⛔ *viele Longs je Asset*, Premium, Käuferanteil, Kontextfläche, Dominanz-Sperren. Befunde 2.668–2.676 |
| **6 · Was darf eine Messung** | Grundgesamtheit `--menge unverzerrt:1..3` **und** `bestand`; Nullwelt Zeitverschiebung (je Asset, **gemeinsam** für Marktmerkmale); **Regeltest** vor jeder Verwendung einer Urteilsregel |
| **8 · Messstandard** | Positivkontrolle, Bekanntheitszeitpunkt und Fehlalarmquote sind geschlossen (Regelwerk § 6, Stand 28.09.) |
| **10 · Nächster Schritt** | ✔ die Altersachse ist gemessen (2.676): gültig, der **24 h alte** Wert trägt am oberen Rand in Suche, Prüfzeit und 2022, die Tagesperiode ist kein Uhrzeit-Artefakt — ⛔ *6 h alt trägt fast nichts* (2.675) war ein Lesefehler. **Kein Blocker** (Nutzer): Alter und A4 werden Gewichte. ⛔ **K1 Schritt 2 als Kurvenmodell gemessen und verworfen** (2.677): trägt in keiner Menge, die Auflösung reicht nicht, der Marktmedian steht für die Zeit — die Wirkung ist aber da (q ungesehen +0,07…+0,10 über der Schätzung, wo *oben gestreckt*). ⛔⭐ **2b gemessen** (2.678): trägt nach dem Vorabkriterium nicht, weil die Auswahl nach Normal + Beitrag vom **Phase-Normal** beherrscht wird (Rückkehr zur Mitte); nach dem Beitrag allein +0,05 in allen vier Mengen — etwa der rsi-Rand allein. ✔ **K5 entschieden (vorläufig): Schwelle auf dem Beitrag** — trägt auch das nicht, wird neu abgestimmt. ➤ dann *Kombination nach dem Beitrag gegen rsi allein* (Pflicht: positiv in jedem Drittel des Normals); **K6** läuft (Voranalyse `Voranalyse_K6_Hebelstufe_28_09.md`, Markpreis wird geladen), dann K7, Simulation Ebene 3, Stammsatz |
| **Werkzeug** | Kettenskripte: der Exit-Code hinter `$(date …)` war immer 0 — Vollständigkeit **am Inhalt** prüfen (Schlusszeile, kein Traceback) |

```bash
python hebel_neubau.py | sed -n '/NEUESTER STAND/,/DIE NAECHSTEN/p'
python hebel_neubau.py | sed -n '/DIE NAECHSTEN MESSUNGEN/,/^---/p'
```

⚠️ Die Pflichtprüfung heißt jetzt **45 Prüfungen** (`--paket Hebelneubau`),
nicht 38. Entscheidungen **E-1 bis E-11** (`Entscheidungen_Hebelneubau.md`).
Der Plan mit dem Stand: `Plan_Hebel_fuenf_Phasen_27_09.md`, Block *Stand 28.09.*

---

## Der eine Befehl, mit dem du anfängst

```bash
python hebel_neubau.py
```

Er gibt den **vollständigen Stand** aus: Hauptplan, Abdeckungen,
Regelwerk, Beitragslage, Zieldefinition, was tot ist, die zwei
Zeitpunkte, die drei Arbeitsmodi, die Auswahlebene, die Messanordnung,
die drei Rollen, die offenen Punkte und alle Befunde ab 2.625.

⭐ **Er kennt den Spot-Arm nicht — nachweisbar:**

```bash
python hebel_neubau.py --nachweis
```

---

# Frage 1 — Woran arbeiten wir?

**Am HEBEL-ARM, und er wird vollständig neu gebaut.** Nutzervorgabe
25.09.2026: *„wir bauen den Hebel-Arm vollständig neu. Wenn Hebel
funktioniert, dann gehen wir zu den anderen Strategien."*

⛔ **SPOT = HEBEL ist tot, für immer und ewig** (Nutzerfestlegung 27.09.).
Die beiden Arme sind nicht dieselbe Frage. Die **einzige** Gemeinsamkeit
ist der **Prüfzeitpunkt**.

⚠️ Der produktive Spot-Arm **läuft weiter** und führt offene Positionen.
Er wird nicht angefasst und ist kein Thema.

**E-8 — mehr gibt es zu Spot im Umbau nicht zu sagen** (Nutzer, 27.09.):

| | |
|---|---|
| Spot in der **heutigen** Form (Code und Produktion) | für den Hebel **tot** |
| Spot-**Quellen** | **nicht** irrelevant — für H20 optimiert und vermessen; nur die **Anwendung** wird auf den Hebel dimensioniert (kurzer, intensiver Handel) |
| Prüfzeitpunkt | **gleichzeitig** — zwei unterschiedliche Prüfungen, **ein Gewinner** |
| später | Spot wird selbst neu gebaut, wenn der Hebel in der ganzen Ablaufkette funktioniert |

```bash
python hebel_neubau.py | sed -n '/WAS ENDGUELTIG TOT IST/,/UEBERTRAGBAR/p'
```

---

# Frage 2 — Was ist das Ziel, genau?

> **OPTIMUM ist: wir kennen die Bewertungen und die LAGE VOR DER
> BEWEGUNG.** Die Bewertung eines bereits gestiegenen Assets ist weder
> das Ziel noch ein Optimum — *„dazu brauche ich kein System, das sehe
> ich am Kurs, und dann steige ich ein und rate."* (Nutzer, 27.09.)

⛔ **Das Ausschlusskriterium:** ein Merkmal, das die **Bewegung selbst**
misst, ist kein Einstiegssignal.

⚠️ **Geprüft wird das mit der KARENZ** — Lage bei `t`, Ereignis erst ab
`t+k`. Bricht der Lift mit wachsendem `k` ein, war er Fortsetzung.

⭐ **Aber die Karenz ist eine ACHSE, kein Filter.** `k=0` ist der
**Betriebsfall** — im Betrieb steigt man sofort ein. `k>0` ist
**Diagnose**. Beide Zahlen werden ausgewiesen, keine kappt die andere.

---

# Frage 3 — Wie sieht der Ablauf zum Prüfzeitpunkt aus?

```
T1  Prüfzeitpunkt
    ├─ BEWERTUNG 1  Einstieg zulässig?   nein | gut | sehr gut
    ├─ BEWERTUNG 2  Hebelhöhe             2× | 3× | 5×
    └─ weiter in der Kette wie heute  ──►  Mail

T2  nach der Eröffnung — Stop, Trailing, Ausstieg   (Phase 5)
```

⚠️ **T1 ist neutral:** kein Kapital, keine Positionsgröße, kein
Ergebniswert, **keine Geometrie**. Es gibt noch keine Position, also auch
keinen Stop.

⚠️ **Die Ablaufkette als Ganzes bleibt die Ausgangsbasis** (Nutzer,
27.09.). Neu gebaut wird **eine Schicht**: die Bewertung.

---

# Frage 4 — Was ist das Regelwerk?

> **Einstieg misst gegen die CHANCE, Hebel gegen das RISIKO.**
> Zwei Zielgrößen, zwei Messungen — ein Merkmal kann in der einen tragen
> und in der anderen nicht.

| | **Bewertung 1** | **Bewertung 2** |
|---|---|---|
| Zielgröße | **Ereignis** (+X % in Y h), regelfrei | **MAE in ATR** |
| Bezug | eigenes Asset (**Lift**) | eigenes Asset |
| Nullpunkt | **Lift = 1** | eigener Durchschnitts-MAE |
| Ergebnis | nein / gut / sehr gut | 2× / 3× / 5× |

`Basisinfos/Regelwerk_Hebel_Bewertung_27_09.md`

---

# Frage 5 — Wo stehen wir? Was trägt, was nicht?

```bash
python hebel_neubau.py | sed -n '/WO WELCHER BEITRAG ZAEHLT/,/DIE NAECHSTEN/p'
```

⛔ **Bis 27.09. abends gab dieser Befehl den Stand VOR 2.651 aus** — und
die Suite erzwang ihn (2.652-beitragslage-nachgezogen). Jetzt nennt jeder
Eintrag seinen Befund, und die Wache leitet aus dem Quelltext der
Messskripte ab. **Die Tabelle unten ist ein Schnappschuss; die Wahrheit
steht im Befehl.**

| Merkmal | Bewertung 1 (k = 0) | Vorlauf | Bewertung 2 | Beleg |
|---|---|---|---|---|
| **`funding` ≤ −0,0040** | ✔✔ belegt, Lift 9,55 — ⚠️ **Vorgriff ungeprüft** | nein | ⬜ | 2.651 · 2.652-vorgriff-funding |
| **`oi_aenderung` ≥ 0,3355** | ✔✔ belegt, Lift 6,23 | nein | ⬜ | 2.651 |
| `konten_verh` ≤ 0,5759 | ✔✔ belegt, Lift 2,96 (nur H6/H12) | nein | ⬜ | 2.651 |
| `momentum_kurz`, `rsi` | ✔✔ belegt, Lift 6,93 / 4,67 | nein | ⬜ | 2.648 / 2.650 |
| **`ema_abstand_atr`** | ⛔ fällt (Richtung runter) | – | ✔✔ **belegt** | 2.642 / 2.647 / 2.648 |
| `turnover` | ⛔ **gemessen, fällt** — nur Bewegung (ein Jahr Messbasis) | – | ⬜ | 2.651 |
| `oi_je_umsatz`, `volumenschub` | ⛔ fällt — nur Bewegung | – | ⬜ | 2.651 |
| `taker_verh`, `top_konten_verh`, `top_summe_verh` | ⛔ fällt — unter dem Suchband | – | ⬜ | 2.651 |
| `vola` | ⛔ nur Bewegung | – | ⭐ Spur (Geometrie) | 2.650 |
| `bandenge` | ⛔ misst nichts | – | ⬜ (vorher „fällt" ohne Befund) | 2.650 |

⚠️ **`funding` unter Vorbehalt:** der gespeicherte Tageswert ist die Summe
der drei Abrechnungen des UTC-Tages und steht an **jeder** Stunde
desselben Tages — ein Anker um 01:00 kennt die Abrechnungen von 08:00 und
16:00. Die Wirkung ist **nicht gemessen**; die Probe ist die nächste
Messung (Frage 10).

⚠️ **Die wichtigste Einschränkung:** **alle** Treffer von 2.651 haben
*Vorlauf nein* — Haltequote 0,29 bis 0,74, unter 0,8. Sie **begleiten**
die Bewegung, sie sagen sie nicht voraus.

⭐ **Und ein Muster, das eine Spur ist:** je länger das Fenster, desto
höher die Haltequote (0,29 bei H6, **0,74** bei H48). Ob sie bei H72 oder
H120 die 0,8 erreicht, ist **nicht gemessen** — das wäre der erste
Beitrag mit echtem Vorlauf.

---

# Frage 6 — Was darf eine Messung, was nicht?

**Drei Arbeitsmodi, sie beantworten verschiedene Fragen:**

| Modus | Phase | Geometrie erlaubt? |
|---|---|---|
| **messen** | 1 | ✔ sie ist Werkzeug, nicht Systemeigenschaft |
| **kalibrieren** | 1 | ⛔ **verboten** — Chance und Risiko steuern |
| **prüfen an Echtdaten** | 2 | ✔ **hier kommt sie zurück**, mit 2×–5× |

⛔ **Die Auswahl ist ASSETEBENE, nie Marktebene.** Nutzerentscheidung
26.09.: *„Das System muss auch bei nur ‚Einem' Asset funktionieren und
nicht besser oder schlechter durch die Watchlist werden."* Absolute
Schwellen in eigenen Einheiten, **keine Fünftel, kein Tagesrang**.

✔ Der Riegel bricht ab:

```bash
python -c "import hebel_neubau as H; H.pruefe_quellen('taeglich_beste')"
```

---

# Frage 7 — Was ist mit der Abdeckung?

⚠️⚠️ **Drei Abdeckungen, die nicht dasselbe sind** — ich habe sie
verwechselt:

| | | |
|---|---|---|
| **Mess** | Anteil der **Anker** mit Wert | funding 99,1 % · turnover 30,0 % |
| **Symbol** | Anteil der **Symbole** | funding 116/116 · turnover **113/116** |
| **Betrieb** | freigegebene Hebelsymbole mit Stundenkursen | **65 %**, mit Laderfix **86 %** |

⛔ `turnover` hat **30 % Zeit-** und **97 % Symbol**abdeckung. Meine
Aussage *„strukturell nicht zu retten"* war falsch.

⚠️ Die härteste Grenze ist die **Liquidität**: nur **15 von 43** Symbolen
erreichen 100.000 USD Medianumsatz je Stunde.

---

# Frage 8 — Welcher Messstandard gilt?

⚠️ **Er steht im CODE, nicht in der Doku:**

```bash
python -c "import messnorm; print(messnorm.standardzeile())"
python pruefe_pakete.py --paket Messstandard
```

**Dazu die SECHS Prüfungen, die jeder Hebel-Befund ab 2.647 belegen muss:**

**Nullwelt** (tagestreu) · **Zeitstabilität** (Kalenderjahre) ·
**Weglassprobe** · **Mehrfachtesten** (Bestes-von-N) · **Ebene** (A/B/C) ·
**je Asset**

Für Bewertung 1 kommt die **Spiegelprobe** dazu — **gerichtet**, Schwelle
**1,717** (geeicht in 2.603). `max(Lift, 1/Lift)` lässt Merkmale durch,
die **Abstürze** vorhersagen.

```bash
python pruefe_pakete.py --paket Hebelneubau
```

⚠️ **Vorbehalt:** die Prüfung liest die `basis` jedes Befundes auf
Stichwörter. Sie erzwingt, dass die Prüfungen **genannt** sind — nicht,
dass sie richtig gerechnet wurden.

---

# Frage 9 — Welche Fehler sind heute passiert? (damit sie nicht wiederkommen)

| | |
|---|---|
| **Riegel zu weit ausgelegt** | `SPOT_QUELLEN` sperrt `funding_fuenftel`; ich habe die Sperre auf die **Rohgröße** `funding` ausgedehnt — und einen ganzen Tag die einzigen drei registrierten Träger nicht angefasst. E-3 gibt Rohgrößen **frei** |
| **Spiegelprobe ungerichtet** | `max(Lift, 1/Lift)` ließ Merkmale durch, die Abstürze vorhersagen |
| **Mehrfachtesten vergessen** | 36 Zellen durchsucht, jede gegen ihr Einzelband — der Fehler von 2.645 |
| **Mindestmenge zählte Anker statt Ereignisse** | ein Jahr mit 0,5 erwarteten Ereignissen kippte einen Befund |
| **Jahr aus dem Index statt aus dem Datum** | die Reihe beginnt am 01.12.2021, „Jahr 2022" lief Dez 2021 bis Nov 2022 |
| **Alles in den Speicher geladen** | ein Dict mit 3,3 Mio Keys (>1 GB) für Daten, die symbolweise verarbeitet werden |
| **Zwei Abdeckungen verwechselt** | siehe Frage 7 |
| **Standblatt nicht nachgezogen — und die Wache hielt es fest** | nach 2.651 stand `BEITRAGSLAGE` weiter auf „ungemessen", und eine Prüfung **verlangte** das. 38 von 38 grün bei falschem Stand. Jetzt leitet die Wache aus dem Quelltext der Messskripte ab (2.652-beitragslage-nachgezogen) |
| **Tageswert an alle Stunden des Tages** | `funding` als Tagessumme an jeder Stunde desselben Tages — möglicher Vorgriff, ungemessen (2.652-vorgriff-funding) |

⭐ **Das Muster dahinter:** melden, bevor fertig geprüft ist. Die
Gegenmaßnahme sind die sechs Prüfungen **vor** der Meldung.

⚠️ **Und der umgekehrte Fehler ist genauso real:** Nutzermahnung
*„bitte wirf nicht alle bisherigen Festlegungen weg, meine Aussagen sind
oft nur Text."* Vor jedem Widerruf: (1) Widerspricht der neue Befund
wirklich — oder beantwortet er eine **andere Frage**? (2) Ist der Hinweis
eine **Anweisung** oder eine **Einordnung**? (3) R-R11: erst
**reproduzieren**.

---

# Frage 10 — Was ist der nächste Schritt?

**In dieser Reihenfolge:**

```bash
python hebel_neubau.py | sed -n '/DIE NAECHSTEN MESSUNGEN/,/^---/p'
```

**Die Messungen** (`hebel_neubau.NAECHSTE_MESSUNGEN`, Stand 27.09. abends):

| # | | |
|---|---|---|
| **1** | **Vorgriffsprobe `funding`** | 2.651 zuerst reproduzieren (R-R11), dann mit dem **Vortageswert d−1** — vorgriffsfrei, ohne Abruf, und die Form, die live beschaffbar ist. **Vorher baut nichts auf `funding` aus 2.651 auf** (2.652-vorgriff-funding) |
| **2** | **Vorlauf bei H72 / H120** | die Haltequote steigt mit dem Fenster (0,74 bei H48). Erreicht sie 0,8? Werkzeug steht: `messe_traeger_auf_bewertung1.py`, nur `ZIELE` erweitern; `funding` in der Form, die die Probe ergibt |
| **3** | **Messung 2 des Regelwerks** | `funding`, `oi_aenderung`, `konten_verh` auf **Bewertung 2** (MAE). Ob Nebenmerkmale, `momentum_kurz`/`rsi` und `bandenge` mitlaufen, entscheidet die Voranalyse (E5) |
| **4** | **`vola` in der Hebelhöhe** | das Register nennt es als Spur: *„über `hebel = verlustanteil / stop_rel` fällt daraus der Hebel"* |

**Unabhängig davon, keine Messung:** **Laderfix 2.611** —
`hole_stundenkurse.handelbar()` (Zeile 114) fragt nur
`api.binance.com/api/v3/exchangeInfo`, die **Spot**-Börse. Die Symbolliste
kommt aber aus dem **Terminmarkt** (Futures). Lösung: zusätzlich
`fapi.binance.com/fapi/v1/exchangeInfo` abfragen, Vereinigung bilden, beim
Kursabruf die passende URL wählen. **9 Symbole, 65 % → 86 %.** ⚠️ Gegen
die echte API testen, nicht blind ändern.

⛔ **Was NICHT mehr gemessen wird:** weitere Kursmerkmale aus der
EMA/RSI/ATR-Familie. Drei unabhängige Messungen (2.578, 2.645, 2.650)
sagen dasselbe.

---

## Die Dokumente, in dieser Reihenfolge

| | |
|---|---|
| `python hebel_neubau.py` | **der Stand** — aus Code, kennt Spot nicht |
| `Basisinfos/Plan_Hebel_fuenf_Phasen_27_09.md` | die **Phasen** (wir sind in 1) |
| `Basisinfos/Regelwerk_Hebel_Bewertung_27_09.md` | wie aus einer Messung eine **Regel** wird |
| `Basisinfos/Entscheidungen_Hebelneubau.md` | E-1 bis E-7, jede fachliche Entscheidung mit Begründung |
| `Basisinfos/Bilanz_Hebelneubau_27_09.md` | was gilt, was gefallen ist |
| `Basisinfos/Ergebnis_Messung1_Traeger_27_09.txt` | der Volltext von 2.651 |
| `python pruefe_pakete.py --paket Hebelneubau` | **38 Prüfungen**, die das alles bewachen |
