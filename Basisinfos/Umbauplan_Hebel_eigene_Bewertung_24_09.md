# Umbauplan — der Hebel bekommt seine eigene Bewertung

**24.09.2026.** Nutzerauftrag: *„bevor wir aufsetzen mach noch eine Runde
(Recherche und Analyse) zum Umbau — **wichtig: das Konzept und der Umbau
darf nicht durch eine fehlende Prüfung oder falsche Annahme etc. während
des Umbaus oder danach kippen**."*

Grundlage: **2.573** (auf H3 trägt `oi_aenderung`), Konzept-Schritt 4 aus
`Konzept_Spot_und_Hebel_trennen_24_09.md`.

---

# ⛔⛔⛔ STAND 24.09.2026 — DER UMBAU IST ABGESAGT. B0 HAT IHN GEKIPPT.

**Befund 2.576.** Ohne das von Trichterstufe 6 gesperrte oberste Fünftel
fällt `oi_aenderung` von **+0,0069 [+0,0031…+0,0108] TRÄGT** auf
**−0,0002 [−0,0032…+0,0030] trägt nicht**. Kontrolle sauber, R-R11
vorher bitgleich reproduziert.

> **Die Wirkung von 2.573 kam aus dem Fünftel, das die Kette nie sieht.**

✔ **Genau dafür war B0 da** — der Plan hatte ihn als *wahrscheinlichste
Abbruchursache* benannt, **bevor** gemessen wurde. Die Abbruchbedingung
in § 4 ist eingetreten und wird nicht nachverhandelt.

⚠️ **Was bleibt:** Schritt A ist gebaut und trägt eigenständig (2.575).
Die Blocker B, C und D bleiben **dokumentiert** — sie treffen jeden
künftigen Versuch einer Instrumenttrennung, nicht nur diesen.

➤ **Der interessantere Rest steht in § 6.**

Alles unterhalb beschreibt den Plan, **wie er vor B0 aussah**. Er bleibt
als Historie stehen.

---

# § 1 Was gebaut werden sollte — in einem Satz

> **`oi_aenderung` bekommt für die Lage `hebel × einstieg` eigene
> Beitragsstufen, die auf H3 gegen die Barrieren-Quote kalibriert sind.
> Die Spot-Bewertung bleibt unverändert.**

---

# § 2 Die Risikoliste — jede Zeile mit Status und Absicherung

| # | Risiko | Status | Absicherung |
|---|---|---|---|
| **1** | **Architektur:** die Hebel-Quote wird in `rollen_lauf.py:2161` aus **denselben** Merkmalen gerechnet wie Spot (2.533) | ✔ **entschärft** | `Beitrag` hat bereits ein **`instrumente`**-Feld, `_gilt()` prüft es (`wahrscheinlichkeit.py:680`). `potential.rechne()` bekommt `instrument` schon übergeben. **Kein neues Feld nötig** |
| **2** | ⚠️ **`oi_aenderung` ist ein SCHALTER** (F-168) — als **Trichterstufe** greift es an **unter 1 %** der Zellen (2.481: 4 von 508 Rollen-Zeilen sind KAUFEN ohne Bestand) | ⛔ **offen — Bauformentscheidung** | **Als BEITRAG bauen, nicht als Trichterstufe.** Sonst wiederholt sich F-180 („nur Einstieg OHNE Bestand, und den gibt es nicht") |
| **3** | ⛔ **Der Bitgleichheitstest deckt `instrument` NICHT ab** — seine 288 Fälle sind crv × stop × klasse × h × gebühr | ⛔ **LÜCKE** | **Test VOR dem Umbau um die Instrument- und Strategie-Achse erweitern**, dann `--aufzeichnen`. Sonst fällt eine Spot-Änderung nicht auf |
| **4** | Die Stufen von `oi_aenderung` sind auf **H20** kalibriert | ⚠️ offen | Neu auf H3 — und **direkt gegen die Barrieren-Quote** (N19-E, 2.568), **nicht** über die Umrechnung `d(q)=d(Potential)/(1+CRV)`. Die überschätzt um Faktor 3 |
| **5** | Die H3-Menge ist **vola-verzerrt**: 48,3 % der Anker fallen heraus, und ruhige Assets lösen öfter auf | ⚠️ bekannt | **Ausweisen, nicht beheben.** Jeder Befund gilt für „Anker, die in 3 Tagen auflösen" |
| **6** | **R-R9**: jede Beitragsänderung verlangt eine neue Schwellenkalibrierung | ⚠️ **Pflicht** | Nach dem Umbau, mit `messe_schwelle_quotengleich.py`. ⚠️ Eine eigene Hebel-Schwelle wäre **eine zweite** Schwelle |
| **7** | **`hebel` hat NULL Signale** in der Produktion — jede Hebelaussage trägt `simuliert=True` | ⚠️ bekannt | Eine Betriebsprüfung braucht Signale. **Bis dahin bleibt der Umbau unbelegt im Betrieb** |
| **8** | **Zwei Messanlagen** (`messnorm.pruefe` / `messnorm_auswahl.pruefe_auswahl`) | ✔ **behoben** | `messnorm.warne_horizont`, beide rufen sie (2.573) |
| **9** | **`KALIBRIERT_FUER`** in `potential.py:677` friert die Stufenlage ein und wird gegen den Istzustand geprüft | ⚠️ offen | Muss im selben Commit nachgezogen werden, sonst schlägt die Prüfung an |
| **10** | Die **Mail** muss die neue Lage erklären — sonst steht dort eine Zahl ohne Begründung | ⚠️ offen | `pruefstand_hebelmail.py` existiert; LONG **und** SHORT prüfen (Lehre aus dem Vorzeichenfehler) |
| **11** | `oi_aenderung` wird an **vier weiteren Stellen** gelesen (`hebel_screening`, `regelwerk_parameter`, `marktrang`) | ⚠️ offen | Das sind **andere Größen** (Screening-Score, Schwelle in Prozent) — **nicht anfassen**, aber vor dem Bau prüfen, dass nichts kollidiert |

---

# § 2b ⚠️⚠️⚠️ Die GESAMTE Ablaufkette — Nutzerhinweis, und er deckt VIER Blocker auf

Die zwölf Trichterstufen (`rollen_gate.STUFEN`):

```
 1 auftrag        Instrument und Strategie erlaubt
 2 fakten         3 lagebild      4 anlass       5 auswahl
 6 terminmarkt    OI-Aufbau nicht im obersten Fuenftel   ← oi_aenderung HEUTE
 7 wiederholung
 8 urteil         Urteil geliefert (LLM-Rolle)           ← kennt die Bewertung nicht
 9 aktion        10 geometrie    11 risikoschicht
12 entscheider    Trefferquote schlaegt den Breakeven    ← hier wirkt die QUOTE
```

## ⛔⛔ Blocker A — **das gemessene Fünftel 4 erreicht die Bewertung nie**

Nicht bloß Doppelzählung. Am Code nachgesehen (`rollen_lauf.py:1608`):

```python
elif _oi_f >= 4:
    durchlauf.verloren(symbol, "terminmarkt",
        "OI-Aufbau im hoechsten Fuenftel ...")
    return          # ← HARTER Abbruch, Stufe 6 von 12
```

Die Sperre greift genau für `strategie == "einstieg"` **ohne Bestand** —
**also exakt die Hebel-Lage.**

> ⚠️⚠️⚠️ **2.573 (+0,0069) ist über ALLE FÜNF Fünftel gemessen. Eines davon
> kommt in der Kette nie an.**

➤ **Ob der Beitrag auf den Fünfteln 0–3 noch trägt, ist UNGEMESSEN.**
Kommt die Wirkung überwiegend aus dem gesperrten Fünftel 4, bleibt nach
der Sperre **nichts** übrig — und der Umbau wäre auf eine Menge kalibriert,
die es nicht gibt.

➤➤ **Pflichtschritt B0, vor allem anderen: 2.573 ohne Fünftel 4
wiederholen.** Das ist eine Messung, keine Entscheidung — genau die
Prüffrage *„BEWERTUNG oder FAKT?"*.

## ⛔ Blocker B — das Instrument ist dort **immer** `spot`, und der Code sagt es

`rollen_lauf.py:2165` rechnet `_hq_quote` mit `instrument=instrument`.
Wörtlich aus dem Quelltext, Zeile 2424:

> *„⚠️ A1: DIE HANDELBARKEIT DER GRUPPE, NICHT DER LAUF. **Seit S6b heisst
> `instrument` fuer Krypto immer "spot"** — ohne diese Zeile ergibt die
> Rechnung nie wieder einen Hebel."*

Und die Reihenfolge ist entscheidend: **die Quote wird VORGEZOGEN**
(Zeile 2130), sie geht in `dimensioniere` ein, und **erst danach** entsteht
das Etikett (`_topf_instrument`, Zeile 2299).

> ⚠️⚠️ **Ein Beitrag mit `instrumente=("hebel",)` würde dort NIE greifen.**

✔ **Heute ohne Wirkung — und genau das ist die Falle.** Nachgesehen:
`instrumente` wird von **keinem** Beitrag gesetzt (nur Felddefinition
`wahrscheinlichkeit.py:146` und Prüfung `:680`). Der falsche Wert fällt
heute niemandem auf und schlägt **erst beim Umbau** zu.

✔ **Lösbar, die Architektur trägt es:** der Aufruf rechnet definitionsgemäß
die **Hebel**quote — die kontrafaktische Frage *„wäre dies ein Hebeltrade,
wie hoch wäre die Quote?"*. `instrument="hebel"` ist dort fachlich korrekt.
**Eine Zeile — aber ohne sie ist der ganze Umbau wirkungslos und niemand
merkt es.** ⚠️ Kein Zirkelschluss: die Frage ist kontrafaktisch gestellt,
die Antwort entscheidet danach über das Etikett.

## ⛔⛔⛔ Blocker C — es gibt einen **Gleichheitswächter**, und er verbietet genau diese Trennung

`rollen_lauf.py:2591`, im Klartext aus dem Quelltext daneben: *„ZWEI STELLEN
RECHNEN DIESELBE QUOTE … weicht sie trotzdem ab, stimmt eine der beiden
Annahmen nicht mehr - und das darf nicht still passieren."*

```python
if (_hq_quote is not None and _potential is not None
        and abs(float(_hq_quote) - float(_potential.quote)) > 1e-9):
    ergebnis.setdefault("fehler", []).append(
        "%s: Quote der Hebelrechnung %.4f weicht von der Bewertung %.4f ab")
```

> ⚠️⚠️⚠️ **Sobald Blocker B gelöst ist und der Hebel-Beitrag greift, weichen
> die beiden Quoten ab — der Wächter meldet dann bei JEDEM Signal einen
> Fehler.**

⚠️ **Er darf nicht ersatzlos weg.** Er schützt vor echtem
Auseinanderlaufen — dieselbe Klasse Schutz, die an mehreren Stellen im
Projekt teuer erkauft wurde.

➤ **Umbau statt Abbau:** der Vergleich prüft heute *„beide rechnen
dasselbe"*. Künftig muss er prüfen *„jede rechnet **zu ihrer Lage**"* —
also die Hebelquote gegen eine Referenz mit `instrument="hebel"`, die
Bewertung gegen eine mit `spot`. Der Wächter bleibt scharf, nur sein
Bezugspunkt wird lagerichtig.

## ⚠️ Blocker D — **drei** Stellen rechnen die Bewertung, nicht eine

| Zeile | Was | Wirkung |
|---|---|---|
| **2162** | `_hq_quote` — die Hebelquote | ⛔ entscheidet über das Etikett (Blocker B) |
| **2579** | `_potential` — die Bewertung | ⛔ Stufe 12, der Entscheider |
| **1192** | `_potential_dazu` — **schreibt `potential_r` ins Signal** | ⚠️ *„SIE ENTSCHEIDET NICHTS: kein Filter, keine Mail, keine Sperre"* |

**Alle drei übergeben `instrument`** — und das ist für Krypto immer `spot`.

⚠️⚠️ **Stelle 1192 ist die heimtückische:** sie entscheidet nichts, aber sie
ist die **Messspur**. Bliebe sie auf `spot`, stünde in jedem Hebelsignal die
**Spot**-Bewertung — und der Umbau wäre **im Betrieb nicht nachmessbar**.
Genau die Stelle, die 2.533 („die Simulation lief auf der alten Schwelle")
schon einmal gekostet hat.

## ⚠️ Abhängigkeit E — die LLM-Rollen (Stufe 8)

`rolle_trader.py` und `rolle_analyst.py` kennen `potential`, `beitrag`,
`funding`, `turnover`, `kelly`, `r(q)` **mit keinem Wort** (2.398). Sie
liefern ihr Urteil in **Stufe 8**, also **vor** der Bewertung in Stufe 12.

| | |
|---|---|
| **Wirkt der Umbau auf die Rollen?** | **Nein** — sie sehen die Quote ohnehin nicht |
| **Muss etwas nachgezogen werden?** | **Nicht für den Umbau.** Aber die Lücke bleibt und gehört in Block **L-ROLLEN** (Plan: *D vor L*) |
| ⚠️ **Risiko** | Wenn Spot und Hebel verschiedene Quoten haben, wird die Erklärungslücke **größer**: die Rolle empfiehlt, ohne zu wissen, nach welchem Maßstab ihr Vorschlag beurteilt wird |

## ⚠️ Abhängigkeit F — Strategien und Empfehlungen

| | |
|---|---|
| **Betroffene Paare** | nur `hebel × einstieg`. `spot × einstieg` (1.537 Zellen) bleibt unberührt, `spot × akkumulation` ist gesperrt, `absicherung` ist Multiasset (2.548) |
| **Die Empfehlung** | entsteht in Stufe 12 aus Quote gegen Schwelle. Zwei Quoten heißen **zwei Schwellen** — sonst vergleicht man Äpfel mit Birnen (R-R9) |
| **Die Mail** | müsste beide Maßstäbe zeigen, sonst steht dort eine Zahl ohne Bezug |

---

# § 3 Die Reihenfolge — und warum sie so ist

| | Schritt | warum zuerst |
|---|---|---|
| **A** ✔ | **ERLEDIGT 24.09.** — Lagenachse gebaut, aufgezeichnet, läuft in der Suite mit (**2.575**) | ⛔ **Risiko 3.** ⚠️⚠️ Dabei kam heraus: der Test war **selbst außer Betrieb** — 432 von 432 rot seit dem 11.09., weil die Suite ihn **nie ausgeführt** hat. Echte Zahlabweichungen: **0**. Und das alte Gitter war auf `instrument` und `richtung` **vollständig blind** (Mutation: 0 FEHL gegen 12 auf der Lagenachse) |
| **B0** | ⛔⛔ **2.573 OHNE Fünftel 4 wiederholen** | **Blocker A.** Fünftel 4 ist von Stufe 6 gesperrt und erreicht die Bewertung nie. Trägt es dort nicht mehr, **entfällt der ganze Umbau** |
| **B** | **Die H3-Stufen messen** — direkt gegen die Barrieren-Quote, out-of-sample (erste Hälfte fitten, zweite prüfen) | Risiko 4. Ohne belegte Stufen gibt es nichts zu bauen. ⚠️ **Auf derselben Menge wie B0** (Fünftel 0–3) |
| **C** | **`oi_aenderung` als Beitrag mit `instrumente=("hebel",)`** eintragen, Spot unverändert — **und alle DREI Aufrufstellen lagerichtig machen** (2162 → `hebel`, 2579 → Bewertung, 1192 → die Messspur) | Risiko 1+2, **Blocker B+D**. ⚠️ Ohne 2162 greift der Beitrag nie; ohne 1192 ist er nicht nachmessbar |
| **C2** | ⛔⛔ **Den Gleichheitswächter (`:2591`) lagerichtig umbauen** — er prüft dann *„jede rechnet zu ihrer Lage"* statt *„beide rechnen dasselbe"* | **Blocker C.** Ohne ihn meldet **jedes** Signal einen Fehler. ⚠️ **Nicht entfernen** — er schützt vor echtem Auseinanderlaufen |
| **D** | **Bitgleichheitstest laufen lassen** — Spot muss **0 FEHL** zeigen | die Abnahme von A |
| **E** | **R-R9**: Schwelle für die Hebel-Lage kalibrieren | Risiko 6 |
| **F** | **`KALIBRIERT_FUER` + Register + Mail-Prüfstand** | Risiko 9+10 |
| **G** | **Suite + Betriebsprüfung am Notebook** | Pflicht bei jeder größeren Änderung |

---

# § 4 ⚠️ Die Abbruchbedingungen — vorab

| | |
|---|---|
| ⛔⛔ **B0: `oi_aenderung` trägt auf den Fünfteln 0–3 nicht mehr** | ⛔ **Abbruch, und zwar sofort.** Dann kam die Wirkung aus dem gesperrten Fünftel 4, und es gibt nichts zu bauen. ⚠️ **Das ist die wahrscheinlichste Abbruchursache** — die Sperre nimmt genau das Extrem heraus, an dem ein Fünftelbeitrag üblicherweise hängt |
| **B liefert keine belegten Stufen** | ⛔ **Abbruch.** Dann ist 2.573 ein Einzelbefund ohne Bauform, und der Umbau entfällt |
| **D zeigt eine Spot-Abweichung** | ⛔ **Sofort zurück.** Die Spot-Bewertung ist M1-Kriterium 1 und **durch** — sie darf sich nicht ändern |
| **E ergibt eine Schwelle, die 0 Signale durchlässt** | ⚠️ **Halt und Rücksprache.** Genau das hat 2.514 für H3 vorhergesagt (bestes Potential 0,1368 → 0,0258 R) |

---

# § 5 Was der Umbau **nicht** leistet — ehrlich vorab

- **Er macht den Hebel nicht wirtschaftlich.** `barriere` ist blind für
  *„wieviel ist zu holen"*; gemessen ist eine Trefferquotenverschiebung
  von **+0,0069**.
- **Er löst die Kelly-Frage nicht.** Ob die Quote damit über
  `1/(1+CRV)` kommt, ist **ungemessen** — und bei H3 lag sie in jeder
  vola-Lage darunter (2.570).
- **Er ist im Betrieb unbelegt**, solange es null Hebelsignale gibt.

➤ **Der Umbau stellt den Hebel auf seine eigene, gemessene Grundlage.
Er verspricht nicht, dass diese Grundlage trägt.**

---

# § 6 ⚠️⚠️⚠️ Was B0 stattdessen gefunden hat — und es wiegt schwerer

**Es fallen ALLE VIER Kandidaten**, nicht nur `oi_aenderung`:

| | mit Fünftel 4 | ohne Fünftel 4 |
|---|---|---|
| `funding` | +0,0002 | **−0,0005** |
| `turnover` | +0,0040 | **+0,0021** |
| `oi_aenderung` | +0,0069 | **−0,0002** |
| `schnitt` | +0,0066 | **+0,0003** |

> **Das oberste OI-Fünftel ist der Ort, an dem in dieser Messung die
> Trennkraft sitzt — für jedes Merkmal. Und genau diese Menge sperrt die
> Kette in Stufe 6 weg.**

## Das ist kein Widerspruch — aber es ist eine offene Frage

⚠️ **2.481 bleibt gültig:** die Sperre trägt **+0,0145 R**. Dort ist die
**Trefferquote** im obersten Fünftel niedriger. Hier **trennen die
Merkmale** dort stärker. Beides kann gleichzeitig wahr sein — eine
schlechte Gegend kann die sein, in der Unterscheiden am meisten bringt.

⚠️⚠️ **Die Frage, die daraus folgt und die noch nie gestellt wurde:**

> Die Kette wirft die Menge weg, auf der die Bewertung am meisten zu
> sagen hätte — und bewertet dann den Rest, auf dem sie fast nichts sagt.
> **Ist „sperren" dort die richtige Bauform, oder wäre „bewerten" besser?**

⛔ **Das ist eine MESSFRAGE, keine Entscheidung** — und sie ist mit dem
vorhandenen Werkzeug beantwortbar: `oi_aenderung` als Beitrag **nur auf
Fünftel 4** gegen die heutige Sperre, auf derselben Zielgröße.

⚠️ **Sie gehört NICHT in den Hebelumbau.** Sie betrifft `spot × einstieg`
genauso — also M1-Kriterium 1, das **durch** ist. Eine Änderung dort
verlangt R-R9 und eine neue Betriebsprüfung.

➤ **Vor jeder weiteren Arbeit daran: Nutzerentscheidung.**

---

# § 7 Was für M1 daraus folgt

| | |
|---|---|
| **Kriterium 1** Spot-Einstieg | ✔ **unberührt** — B0 hat die Spot-Bewertung nicht angefasst |
| **Kriterium 2** Hebel gemessen | ⛔ **weiter nicht erfüllt.** Der Hebel hat auf seinem eigenen Horizont **keinen** tragenden Beitrag auf der Menge, die die Kette sieht |
| **Betriebsrisiko** | **keines** — es wurde nichts am Betrieb geändert |

⚠️⚠️ **Die ehrliche Lage:** der Weg „eigene Hebelbewertung" ist mit den
vorhandenen Beiträgen **zu Ende gemessen**. 2.490 (H20) sagte es, 2.573
(H3) schien es zu widerlegen, B0 zeigt: der Unterschied lag an einer
Menge, die im Betrieb nicht existiert.

➤ **Das ist kein verlorener Tag.** Ohne B0 wäre ein Beitrag gebaut
worden, der im Betrieb **nachweislich nichts** bewirkt — und niemand
hätte es gemerkt, weil die Stufen auf der vollen Verteilung kalibriert
gewesen wären.
