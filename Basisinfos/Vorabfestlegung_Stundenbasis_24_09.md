# Vorabfestlegung 10 — der Hebel auf der Stundenbasis

**24.09.2026, geschrieben VOR der Messung.** Nachfolger von
Vorabfestlegung 9, nachdem 2.582 die Zielgröße korrigiert hat.

**Nutzeraufträge:** *„nimm noch 6h dazu"* · *„prüfen und gegenprüfen"*

---

# § 1 Warum diese Messung überhaupt möglich wird

**Gemessen am 24.09. (2.582):**

| H | Stop % | **offen %** | Ziel \| entschieden |
|---|---|---|---|
| 2 Tage | 29,5 | **61,3** | 23,7 % |
| 20 Tage | 63,3 | 4,8 | 33,5 % |

➤ **Bei kurzen Haltedauern bleibt die Mehrheit der Trades offen.** Sie enden
weder im Ziel noch im Stop, sondern **durch Entscheidung** — und ihr
Ergebnis ist der Zwischenstand beim Ausstieg.

⛔ **Auf Tagesdaten kennen wir diesen Kurs nicht.** Deshalb war der kurze
Horizont bisher nicht bewertbar, und deshalb hat jede Messung dort nichts
gefunden: sie sah ein Drittel der Wirklichkeit, und zwar das ungünstigste.

✔ **Die Stundenkurse schließen genau diese Lücke** (`data/stundenkurse.db`,
117 Symbole, 3,24 Mio Stunden — gegengeprüft: Tagesschlüsse bitgenau
identisch zu `messdaten.db`, Abdeckung 100,00 %).

---

# § 2 Die Zielgröße — neu und hier definiert

> **`ergebnis_r`: was der Trade beim Ausstieg tatsächlich einbringt,
> in Stopeinheiten.**

| Fall | Wert |
|---|---|
| Ziel zuerst getroffen | `+CRV` |
| Stop zuerst getroffen | `−1` |
| **im Fenster keins von beiden** | ⭐ **`(Kurs − Einstieg) / Stopabstand`** — der Stundenschlusskurs am Ende der Haltedauer |

⚠️⚠️ **Der dritte Fall ist der Kern** und der Unterschied zu `barriere`. Er
ist bei 6–24 h die **Mehrheit**.

| | |
|---|---|
| **Statistik** | **Median** — wie `bewegung_r`, aus demselben Grund: kontinuierlich und ausreißeranfällig |
| **Gebühren** | ⛔ **keine.** Regel 2 — die Bewertung bleibt neutral, die Finanzierung erscheint in der Mail |
| **Eintrag in die Norm** | ⛔ **nicht**, solange sie unbelegt ist. Eine Zielgröße in `ZIELGROESSEN` ist eine Zusage |

⚠️ **Sie wird NICHT über `pruefe_auswahl` gefahren** — die Norm erzwingt
für `hebel × einstieg` die Zielgröße `barriere` und würde abbrechen. Das ist
richtig so. Diese Messung läuft deshalb über `messnorm.pruefe` mit
ausdrücklicher Begründung, wie die Norm es vorsieht: *„wer bewusst eine
andere misst, ruft `messnorm.pruefe` und begründet es im Befund."*


## 2.1 ⚠️⚠️⚠️ Der Nutzereinwand — und was er gemessen bedeutet

**Nutzer, 24.09.2026:** *„bei Krypto sind Bewegungen oft schnell kurz höher —
wie auch die Gegenbewegungen"*

**Sofort gemessen** (`messe_scharfe_bewegungen.py`, 25 Symbole, 86.800 Anker,
Produktionsgeometrie, LONG). ⚠️ Der Einwand trifft **die Zielgröße selbst**:

| H | Schluss | **MFE** | **MAE** | stand >1 R, schloss darunter |
|---|---|---|---|---|
| 6 h | +0,000 | **+0,204** | −0,214 | 2,1 % |
| 24 h | −0,022 | **+0,420** | −0,454 | 9,5 % |
| 72 h | −0,061 | **+0,752** | −0,812 | ⭐ **21,1 %** |

➤ **Bei 72 h stand jeder fünfte Trade zwischendurch über +1 R und schloss
darunter.** Der Schlusskurs sieht davon **nichts**.

➤ **Und die Gegenbewegung ist die schärfere:** MAE ist durchweg **größer**
als MFE (72 h: −0,812 gegen +0,752).

### ⚠️⚠️ Was daraus folgt — und was ausdrücklich NICHT

| | |
|---|---|
| ✔ **`ergebnis_r` bleibt die Zielgröße** | sie ist **handelbar**. MFE ist es nicht — man steigt nicht am Hoch aus, wenn man es nicht vorher kennt (Messstandard 08.09.: *„ein Maximum ist kein Schätzer"*) |
| ✔ **MFE und MAE laufen als AUSWEIS mit** | als Ober- und Untergrenze des Erreichbaren, nie als Ergebnis |
| ⭐ **Der Einwand deckt eine ANDERE Frage auf** | wenn 21 % über 1 R standen und darunter schlossen, ist das eine **AUSSTIEGSfrage**, keine Einstiegsfrage. Eine feste Haltedauer lässt diesen Betrag liegen |
| ⛔ **Sie wird hier NICHT beantwortet** | ein Trailing-Stop oder Teilausstieg ist eine **zweite Baustelle**. Zwei Dinge gleichzeitig zu ändern macht beide unzuordenbar — die stehende Regel *„erst die Ursache messen, dann die Form"* |

➤ **Aufgenommen als eigener Punkt: der Ausstieg ist eine offene Stellgröße
des Hebelgeschäfts, gleichrangig mit dem Einstieg.** Einzuordnen nach dieser
Messung.

## 2.2 ✔ Die Auflösungsgrenze ist gemessen, nicht angenommen

**Berührt eine einzelne Stunde beide Barrieren, ist die Reihenfolge auch auf
Stundenbasis unbekannt.** Auf Tagesbasis war das der Hauptfehler.

| | **mehrdeutig** |
|---|---|
| Produktionsgeometrie, 6 h … 72 h | **0,00 – 0,01 %** |
| Stop mitskaliert (`× √(H/24)`), 6 h | **0,04 %** |

✔ **Die Stundenbasis trägt die Reihenfolge.** ⚠️ Sie tut das, weil Ziel und
Stop weit auseinander liegen (Stop 5–25 %, Ziel doppelt so weit) — die
Aussage gilt **für diese Geometrie**, nicht allgemein.

## 2.3 ⚠️ Der Stop wird als zweite Achse mitgeführt

Ein auf Tagesbewegung ausgelegter Stop ist für ein 6-h-Fenster zu weit.
**Gemessen**, beide Varianten nebeneinander:

| H | Prod: Ziel \| Stop | **skaliert: Ziel \| Stop** |
|---|---|---|
| 6 h | 0,4 % \| 2,8 % | **2,7 % \| 14,6 %** |
| 24 h | 3,4 % \| 16,2 % | 3,4 % \| 16,2 % |
| 72 h | 12,7 % \| 39,8 % | **4,2 % \| 17,7 %** |

➤ **Mit `× √(H/24)` wird die Ausgangsverteilung über alle Haltedauern fast
konstant** — die Signatur einer haltedauerneutralen Geometrie.

⚠️⚠️ **Aber die bedingte Trefferquote bleibt unter der Kelly-Nullstelle:**
6 h skaliert → 2,7/(2,7+14,6) = **15,6 %**, 72 h Produktion → **24,2 %**;
die Nullstelle ist **33,3 %**. ➤ **Auf der ungefilterten Menge verliert der
kurze Hebeltrade strukturell.** Genau das ist die Nullhypothese, die die
Kandidaten aus § 4 schlagen müssen — sie ist jetzt **beziffert**.

---

# § 3 Die Haltedauern — Achse, nicht Vorgabe

> **6 h · 12 h · 24 h · 48 h · 72 h**

**Warum diese fünf:**

| | |
|---|---|
| **Untergrenze 6 h** | Nutzerentscheidung 24.09. Darunter wird es **nicht messtechnisch**, sondern **praktisch** eng: das Signal muss ausgeführt *und* der Ausstieg erreicht werden |
| **Obergrenze 72 h** | rund die 3 Handelstage, mit denen der Betrieb heute rechnet (2.513) |
| **Warum eine Achse** | weil die Haltedauer eine **Stellgröße** ist, keine Beobachtung. Die „0,30 Tage" aus 2.493 sind eine **Annäherung** über 188 Positionen — keine Vorgabe |

⚠️ **Der Stop bleibt vorerst aus dem TAGES-ATR.** Das ist bekannt zu weit
für einen 6-h-Trade und wird **ausgewiesen, nicht behoben** — sonst ändern
sich zwei Dinge gleichzeitig und keines ist zuzuordnen.

---

# § 4 Die Kandidaten — mit Hypothese, nicht blind

**Aus den sieben stündlichen Größen**, jede mit einer **fachlichen
Erwartung vor dem Lauf** (Methodik 2.80):

| # | Kandidat | Hypothese | erwartete Richtung |
|---|---|---|---|
| **K1** | `oi` — Veränderung über 6 h | frischer Positionsaufbau geht Bewegung voraus | **offen** — Aufbau kann in beide Richtungen |
| **K2** | `taker_verh` — Niveau | aggressive Käufer gegen Verkäufer, der unmittelbarste Druck | **positiv** bei Käuferüberhang |
| **K3** | `taker_verh` — Veränderung über 6 h | der **Umschwung** im Druck, nicht sein Niveau | **positiv** bei Drehung nach oben |
| **K4** | `top_konten_verh` **minus** `konten_verh` | ⭐ **große gegen kleine Konten** — stehen sie gegeneinander? | **positiv**, wenn die Großen long sind und die Masse nicht |
| **K5** | `konten_verh` — Extremlage | sehr einseitige Retail-Positionierung → Squeeze-Gefahr | **negativ** am Extrem |
| **K6** | `oi_wert` / `oi` — Veränderung | die **Durchschnittsposition** wächst oder schrumpft | offen |
| **KON** | `zufall` | **Kontrolle** — muss null ergeben | null |

⛔ **`punkte` wird ausgeschlossen:** Werte 9–12, Median 12 — das ist ein
**Vollständigkeitsmaß** der Datenquelle, kein Marktmerkmal. Es als
Kandidaten zu führen hieße, die Datenlage zu messen (Regel 4).

## 4.1 ⚠️ Der Suchpreis — vorab benannt

**6 Kandidaten × 5 Haltedauern = 30 Kombinationen.** Bei 5 % Fehlerrate
wären **1,5 Zufallstreffer** zu erwarten.

➤ **Poisson gegen die Erwartung** (Methodik 2.477): ein Befund gilt erst,
wenn die Trefferzahl die Erwartung **signifikant** übersteigt — nicht, wenn
irgendeine Zelle grün ist.

⚠️ **Und die Form zählt:** ein echter Effekt zeigt sich über **benachbarte**
Haltedauern, nicht in einer einzelnen Zelle.

---

# § 5 Die Norm

| | |
|---|---|
| **Frageart** | `beitrag` → **selektierte Menge** (F-212) |
| **Bezug** | **Nullpunkt** aus 40 Nullwelten, 90. Perzentil |
| **Trennschärfe** | gegen denselben Bezug, gepflanzte Stärken bis 0,40 R |
| **Positivkontrolle** | 5 Ziehungen |
| **Negativkontrolle** | `zufall` — **Pflicht, nicht Kür** (die Lehre vom 24.09.) |
| **Blocklänge** | ⚠️ `_block` ist auf **Handelstage** ausgelegt. Bei Stundenauflösung wird die Blocklänge in **Stunden** gerechnet und die Zahl der Blöcke ausgewiesen — unter 20 Blöcken gilt **kein Befund** |
| **Abgrenzung** | **nur Krypto** |

## 5.1 Was mitläuft

1. **R-R11 gegen 2.582:** die Anteile (Ziel/Stop/offen) müssen sich bei
   72 h den Tageswerten von H3 annähern. Tun sie das nicht, stimmt die
   Stundenrechnung nicht.
2. **Der Anteil offener Trades** je Haltedauer — er ist das Maß dafür, wie
   stark die neue Zielgröße überhaupt wirkt.
3. **Beide Historienhälften** (B6).
4. **Die Belegung je Fünftel** — eine Stufe aus zwölf Ankern ist keine.

---

# § 6 Die Entscheidungsregel — VOR der Messung

| Ergebnis | Entscheidung |
|---|---|
| **R-R11 fällt** (72 h ≠ Tagesbild) | ⛔ **Stopp** — die Stundenrechnung ist das Problem |
| **Ein Kandidat trägt** über **benachbarte** Haltedauern, Kontrolle sauber, über der Poisson-Erwartung | ✔ **Der Hebel hat eine Grundlage.** Danach: Stufen kalibrieren, R-R9, Betriebsprüfung |
| **Nur EINE Zelle trägt** | ⚠️ **kein Befund** — das ist die Signatur eines Zufallstreffers |
| **Keiner trägt**, Trennschärfe reicht | ⛔ **Auch auf der richtigen Auflösung trägt nichts.** Dann ist der Hebel mit den *vorhandenen Datenquellen* nicht zu begründen — und die Frage geht an **neue Quellen** oder an M1 |
| **Trennschärfe reicht nicht** | ⚠️ nichts entschieden — Datendecke |
| **Kontrolle trägt** | ⛔ Lauf ungültig |

⚠️⚠️ **Wird nicht nachverhandelt.**

## 6.1 Die Vorhersage, vor dem Lauf

**Erwartung: K2 oder K3 (`taker_verh`) trägt auf 6–12 h, die übrigen nicht.**
Begründung: der Taker-Druck ist die einzige der sieben Größen, die eine
**unmittelbare Handlung** misst statt eines Bestands — und er ist bei kurzen
Haltedauern am ehesten wirksam.

**Gegenthese:** K4 (große gegen kleine Konten) trägt, weil es die einzige
Größe ist, die eine **Gegenüberstellung** enthält statt eines Niveaus.

⚠️ **Ein Nullbefund bleibt das wahrscheinlichste Ergebnis.** Neu ist allein,
dass er dann etwas anderes bedeutet als bisher: nicht *„falsch gemessen"*,
sondern *„auf der richtigen Auflösung nicht vorhanden"*.

---

# § 7 Was diese Messung **nicht** entscheidet

- **Nicht** die Stopweite — sie bleibt aus dem Tages-ATR und wird
  ausgewiesen (§ 3).
- **Nicht** Takt und Cooldown. ⚠️ Nutzerhinweis 24.09.: *„der Takt ist
  ohnehin ein Thema beim Hebel, und der Cooldown ist eine künstliche
  Grenze, die verringert werden sollte, wenn das System funktioniert"* —
  **vorgemerkt, einzuordnen nach der Ablaufkette.**
- **Nicht** den **Ausstieg**. ⚠️ § 2.1 hat ihn als eigene Stellgröße
  sichtbar gemacht (21 % der Trades standen über 1 R und schlossen darunter)
  — **vorgemerkt, nicht hier beantwortet.**
- **Nicht** die Ausführbarkeit. Ob ein 6-h-Trade im Alltag umsetzbar ist,
  ist eine Frage an den Betrieb, keine Messfrage.
- **Nicht** M1.
