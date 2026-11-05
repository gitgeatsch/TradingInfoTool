# Voranalyse G7 S7-Anlage — wie die Asset-Urteile von S7 gemessen werden (05.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag:** Nutzer 05.11.: *„S7-Anlage zuerst“*
**Grundlage:**
- [`Voranalyse_G7_Stufe1_04_11.md`](Voranalyse_G7_Stufe1_04_11.md): S1-3 (S7 ist eine andere Messung), §4 (Vorabfestlegung), §5.1 (S7 zuletzt), §5.2 ⚠ (S7 ohne Kursreaktion)
- [`Voranalyse_G7_Messplan_02_11.md`](Voranalyse_G7_Messplan_02_11.md): §3 Messplan, §11 Stufe-3-Anlage (Tages-Nullwelt)
- [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) §3a: Frage S7, F3 *eingepreist*

**Stand:** nur Vorprüfung. Zwei Skripte, beide nur lesend, ohne LLM. **Kein S7-Urteil existiert, kein Urteil des laufenden Laufs wurde
gegen Kurse gehalten.**
- `Rechenkern_02_10/g7_s7_voranalyse.py` → `g7_s7_voranalyse.txt`
- `Rechenkern_02_10/g7_s7_aufloesung_grob.py` → `_grob.txt`, `_grob_b.txt`, `_grob_c.txt`

**Termin:** Der Lauf von Stufe 1 erreicht S7 nach 1.760 Aufrufen, also ≈ **08.11. vormittags** (gemessen ≈ 200 Aufrufe/h, der Tagestopf ≈ 480 ist jeweils mittags leer und kommt um 09:00 zurück). Bis dahin müssen Anlage, Selbsttest
und Vorabfestlegung stehen, und die Frage in §4 muss entschieden sein.

---

## 0. Worum es geht

S1–S4 und S8 urteilen **einmal je Tag über den Markt**, gemessen gegen BTC oder die Breite mit der Anlage aus Stufe 0b. S7 urteilt
**je Asset**: Für jedes Asset, das von einer Meldung direkt betroffen ist, gibt es „stützt“, „belastet“ oder „keine“. Gemessen wird
gegen den Ertrag **dieses** Assets. Das ist eine andere Einheit (Asset × Tag), eine andere Ballung und eine andere Streuung. Nach dem
Memory *Selbsttest vor dem ersten Blick bei jeder neuen Nullwelt* braucht S7 deshalb eine eigene Anlage, bevor das erste S7-Urteil
entsteht.

---

## 1. Der Messrahmen — gemessen

Eine **Zelle** ist (Stichtag T, Asset a), wenn in der S7-Eingabe von T mindestens eine Ereigniszeile a betrifft. Die Eingabe ist
genau die des Laufs (`sichten_gutachten.eingabe`), Assets = REGEL0-Menge zum Zeitpunkt + Kern.

| | |
|---|---|
| Zellen | **9.552** an allen 335 Tagen, 379 Assets; je Tag Median 26, P90 51, höchstens 70 |
| davon mit Zielgröße | **9.398 (98,4 %)**. Es fehlen neue Werte ohne 60 Tage Geschichte (OPG, GENIUS, CAP …) |
| Blöcke à 15 T | **23** (Mindestzahl 20). Das reicht, aber knapp |
| Kern BTC/ETH/SOL | 9,9 % der Zellen. BTC und ETH haben an fast jedem Tag eine Meldung (327 / 326 Tage) |
| Quellen der Zeilen | Nachrichten 9.397 · Binance 5.509 · Upbit 636 |
| Typen (Zeilen) | paar_entfernt 2.861 · unternehmen 2.460 · netz_upgrade 1.634 · etf_fonds 1.546 · delisting_margin 1.531 · regulierung_klage 1.021 · listing_spot 1.003 · hack_exploit 879 · … |
| Schwankung über 3 T (σ√3) | Median **7,3 %** (P25 5,7 %, P75 9,3 %). 0,2 σ ≈ 1,5 %, 0,3 σ ≈ 2,2 % |

---

## 2. Befunde

### S7-1 Die Ballung ist stark: die Einheit ist der Lauf, nicht die Zelle

Eine Meldung steht **7 Tage** in der Eingabe (`FENSTER_T`). Deshalb gilt:
- **88,9 %** der Zellen standen schon am Vortag da.
- Nur 11,4 % haben eine Meldung, die jünger als 24 h ist.
- Je Asset gibt es **1.065 Läufe**, Länge im Median 7 Tage.

Ein LLM, das dieselbe Meldung sieben Tage gleich liest, gibt sieben gleiche Urteile, auf sich überlappenden 3-Tage-Erträgen.
**Wer die 9.552 Zellen als unabhängig zählt, misst Scheingenauigkeit.**

### S7-2 Die Nullwelt — vier Wege vorgeprüft, einer bleibt

Künstliche Urteile, echte Zielgrößen, je 200 Ziehungen (20 bei der Tagesbahn). Fehlalarm in %, Sollwert ≤ 5. Standardfehler bei 200
Ziehungen ≈ 1,5 Pp.

| Erzeuger (wie ein Urteil aussehen kann) | **Asset-Zeit, studentisiert** | Asset-Zeit, Mittelwertdifferenz | Asset-Ereignis | Tagesbahn (Stufe 3) | naiv (t-Test) |
|---|---|---|---|---|---|
| G-Lauf 2/Tag (ein Urteil je Lauf) | **6,5** | 7,5 / 7,5 / 8,0 | 10,0 | 10,0 | 15,0 |
| G-Lauf 5/Tag | **5,5** | 9,0 / 6,0 / 5,0 | 6,0 | 5,0 | 20,5 |
| G-Asset 5 % (Asset-Vorurteil) | **4,0** | 4,5 / 5,5 / 5,5 | 36,5 | 0,0 | 14,5 |
| G-Markt L = 3 (Tagesstimmung) | **3,0** | 5,5 / 5,5 / 3,5 | 12,5 | 0,0 | 18,0 |
| G-Markt L = 10 | **5,0** | 5,0 / 2,0 / 5,0 | 14,0 | 0,0 | 21,0 |

Die einzelnen Wege:
- **Asset-Zeit:** Die Urteilsreihe **jedes Assets** wird um **dasselbe** k Tage im Kreis verschoben, über die volle Bahn
  (k = 1 … 334). Dabei bleibt dreierlei erhalten: das Urteil beim Asset (ein Asset-Vorurteil zählt nicht als Wert, Regel 3), der Lauf
  als Ganzes und der gemeinsame Markttag.
- **Asset-Ereignis:** wie Asset-Zeit, aber nur innerhalb der Ereignistage des Assets. Es zerreißt Asset und Markttag und wird
  **verworfen** (36,5 %).
- **Tagesbahn:** Sie reißt die Läufe je Asset auseinander, das Ergebnis ist instabil.
- **Naiv:** unbrauchbar, so wie es S7-1 erwarten lässt.

⚠️ **Warum Asset-Zeit ohne Studentisierung zu hoch liegt:** Die Verschiebung setzt die Urteile auf Tage **ohne** Meldung, und dort
streut die Zielgröße weniger als an Meldungstagen. Wird die Statistik durch ihren eigenen Standardfehler geteilt (studentisiert), fällt
diese Streuung heraus. Das bringt 3–6,5 % statt 4,5–9 %. **Ob das Soll gehalten wird, entscheidet erst der Selbsttest mit 1.000
Ziehungen im Bau.**

**Vorschlag für den Bau** (ohne eigene Frage, wie bei Stufe 3):
- Hauptstatistik **t = (Mittel stützt − Mittel belastet) / Standardfehler**, Nullwelt **Asset-Zeit**, einseitig **oben**.
- Liegt der Fehlalarm im Selbsttest über der Toleranz von **6,5 %** (wie Stufe 3), wird das Band aus dem Selbsttest **geeicht**: Es
  gilt das kleinste Perzentil, bei dem alle Erzeuger ≤ 5 % liegen. Diese Eichung wird festgeschrieben, **bevor** ein S7-Urteil existiert.

### S7-3 Die Auflösung (grob, studentisiert)

Gepflanzt sind `z + s` an „stützt“ und `z − s` an „belastet“. Die Urteile folgen den Läufen.

| Urteile je Tag | 0,1 σ (≈ 0,7 %) | 0,2 σ (≈ 1,5 %) | 0,3 σ (≈ 2,2 %) | 0,5 σ |
|---|---|---|---|---|
| 2 (wie in der Probe) | 42 % | **82 %** | 98 % | 100 % |
| 5 | 65 % | **98 %** | 100 % | 100 % |

**Lesart:** Ein Unterschied von ≈ 1,5 % über 3 Tage zwischen „stützt“ und „belastet“ würde mit 4 von 5 gefunden. Das ist besser als
bei den Tagessichten (≈ 0,5 σ, Stufe 1 S1-1). S7 hat mehr Einheiten, nämlich 1.065 Läufe statt 22 Blöcke.

### S7-4 Gemessen wird die RICHTUNG, und der Vergleich ist eine Regel ohne LLM

Die Hauptstatistik vergleicht „stützt“ mit „belastet“, **beide auf Meldungstagen**. Sie misst also, ob das LLM die **Richtung** einer
Meldung trifft, und nicht, ob es eine Meldung gibt. Das passt zur Vorabfestlegung (Stufe 1 §4): „einseitig unten bei belastet, oben
bei stützt“.

**Vergleichsarm ohne LLM, mit gleicher Rate** (Messplan §3 Stufe 2):
- Eine **Typ-Regel**: hack_exploit, delisting_*, depeg_aussetzung, monitoring → belastet · listing_*, etf_fonds, airdrop,
  netz_upgrade → stützt.
- Auf der gleichen Zahl von Zellen je Seite, gewählt nach Schwere oder Zahl der Meldungen.

Das LLM **bringt etwas** nur, wenn es über der Typ-Regel liegt, mit Abstand außerhalb des Bands derselben Nullwelt. Die Typ-Regel ist
der ehrliche Vergleich: Sie weiß, *was* passiert ist, aber nicht, was es *bedeutet*.

### S7-5 Die Zielgröße beginnt eine Stunde nach dem Stichtag, nicht am Tagesschluss

**Festlegung:** `ertrag_s = ln(P[T 01:00 + 72 h] / P[T 01:00]) / (σ_a · √3)`, σ_a aus den 60 Tagen vor T.

Bei S1–S4 beginnt die Zielgröße am Tagesschluss von T. Bei S7 würde das die ersten 24 h nach dem Urteil verschenken, und
Asset-Meldungen wirken in Stunden. Die eine Stunde ist der Leseverzug wie in A1 (`LESEVERZUG_H`): Das Gutachten entsteht nach
00:00.

**Auskunft dazu**, nie hochgestuft:
- H = 1 und H = 5,
- nur Zellen mit Meldung < 24 h (1.087),
- Weg b getrennt (Stufe 1 S1-4),
- Kern getrennt.

### S7-6 „Eingepreist“ ist ohne Kurs geraten — die Kursreaktion wäre da

In der Probe sagte S7 bei „eingepreist“ fast immer „teilweise“. Die Eingabe enthält aber **keinen** Kurs je Asset: F3 (*„hat der
Kurs schon reagiert?“*) ist so nicht beantwortbar, das Feld wäre Rauschen.

Gemessen, als **Fakt** über die Gegenwart (Regel 4: kein Auslöser, nur Eingabe):

| | |
|---|---|
| Kursreaktion ln(P[T] / P[Stunde der Meldung]) | für **99,8 %** der Zellen vorhanden |
| gegen BTC | Betrag Median **3,1 %**, P10 −9,7 %, P90 +5,8 % |
| Alter der Meldung | Median 101 h. Der Kurs hatte also meist Tage Zeit zu reagieren |
| live am NB | Stundenkurse der REGEL0-Menge laufen stündlich (`regel0_nachlader`). Für Bestände ohne Binance-Spot (CANTON, AERO nur Futures) fehlt sie → „unbekannt“ |

→ **Frage §4.**

### S7-7 Nebenbefund aus dem laufenden Lauf: zwei Arten Prüfer-Beanstandung, die keine Faktenfehler sind

Stand 05.11. 08:06 (98 S1-Gutachten): 6 beanstandet, nur Form und Treue angesehen, kein Kurs.
- **5 Fälle:** Unter `wert` steht der **zweite** Wert der Zeile (BTC „−29,2“ = Abstand zum 200-T-Schnitt, OI „−20,0“ = Veränderung
  über 30 T) statt des ersten. Die Zahl steht in der zitierten Zeile, sie ist nur dem falschen Feld zugeordnet.
- **1 Fall: ein Fehler in Prüfer v2.** In der Zeile steht `-2.43e-05 %` (Funding), `angezeigt()` liest daraus −2. Das Modell hatte
  den Wert exakt übernommen.

**Kein Abbruch nötig:** Eingabe und Rohantwort jedes Gutachtens sind abgelegt, die Treue lässt sich in Stufe 2 mit einem
berichtigten Prüfer neu rechnen. Der Hauptlauf nimmt ohnehin alle Gutachten (Stufe 1 S1-7). **Vorschlag für Stufe 2:** Prüfer v2.1
liest die e-Schreibweise und weist den zweiten Wert (`mass_wert`) als eigene Art „Feld vertauscht“ aus, getrennt von „falscher Wert“.
Dazu kommt ein eigener Selbsttest, vor dem Neurechnen.

---

## 3. Bauplan (ohne LLM)

| # | Was | Wo |
|---|---|---|
| B1 | **Anlage:** Panel Asset × Tag aus der Eingabe des Laufs, Zielgröße nach S7-5, t-Statistik, Nullwelt Asset-Zeit (volle Bahn), Arme nach §4 der Vorabfestlegung | `Rechenkern_02_10/g7_s7_anlage.py` |
| B2 | **Selbsttest** 1.000 Ziehungen je Erzeuger (G-Lauf 2/5, G-Asset, G-Markt 3/10, dazu **G-Typ**: Urteile nach der Typ-Regel auf echten Zielgrößen, als Prüfung, dass die Anlage einen Typ-Effekt nicht dem LLM gutschreibt); Pflanzung als Auflösungskurve; ggf. Eichung des Bands (S7-2) | dto. → `g7_s7_anlage.txt` |
| B3 | **Vergleichsarm** Typ-Regel (S7-4), bei §4 a zusätzlich eine **Kurs-Regel** (Kursreaktion gegen BTC → Gegenrichtung oder Fortsetzung, beide ausgewiesen), gleiche Rate wie das LLM | dto. |
| B4 | **Vorabfestlegung S7** in Stufe 1 §4 nachtragen (Statistik, Nullwelt, Band, Arme, Auskunft) und **committen vor dem ersten S7-Aufruf** | `Voranalyse_G7_Stufe1_04_11.md` |
| B5 | bei §4 a: **S7-Eingabe** um die Kursreaktion je Asset ergänzen (neue S7-Prompt-SHA), Prüfpaket `SichtenGutachten` erweitert (kein Vorgriff: Kurs nur bis T 00:00), Probe 3 Tage nur S7 | `agent/sichten_gutachten.py` |

Prüfpaket für B1: Kunstpanel mit bekannter Wahrheit (keine echte Messung), wie `G7Messanlage`.

---

## 4. Zur Abstimmung — eine Frage: Kursreaktion in die S7-Eingabe?

| | Weg | Folge |
|---|---|---|
| **a** | **ja**: Je Asset-Zeile steht als Fakt *„Kurs seit Meldung ±x %, gegen BTC ±y %“* | F3 wird beantwortbar. Die Frage S7 bleibt, wie in §3a entschieden. Neue S7-Prompt-SHA vor dem ersten S7-Aufruf, also keine Doppelaufrufe. **Risiko:** Das LLM folgt nur dem Kurs (*LLM-Urteile über dieselben Zahlen trennen nicht*). Das wird **gemessen**: Die Kurs-Regel im Vergleichsarm (B3) zeigt, ob das LLM mehr liest als den Kurs |
| b | nein: „eingepreist“ wird als „unbekannt“ verlangt | sauberer Test des reinen **Textverständnisses**. F3 bleibt offen, das S7-Gutachten ist gegenüber §3a unvollständig. Das finale LLM bekommt den Kurs je Asset ohnehin (Datenbasis §3), aber nur bei REGEL0-Einstiegen |
| c | beides: S7 zweimal laufen lassen, mit und ohne Kurs | misst direkt, was der Kurs am Urteil ändert. ≈ 350 Aufrufe mehr, der Lauf endet ≈ 0,7 T später. Die Frage gehört eigentlich in Stufe 4 (Beitrag mit/ohne) |

**Empfehlung a.**
- F3 ist Teil der entschiedenen Frage. Ohne Kurs ist das Feld geraten.
- Die Kursreaktion ist ein Fakt der Gegenwart, ist am NB für die REGEL0-Menge stündlich da und ist im Rückspiel zu 99,8 % vorhanden.
- Das Risiko „folgt nur dem Kurs“ wird nicht unterstellt, sondern gegen die Kurs-Regel gemessen.
- c kostet Zeit für eine Frage, die Stufe 4 beantworten soll.

**Danach, ohne weitere Frage:** B1–B5 bauen, Selbsttest, Vorabfestlegung committen. Alles muss stehen, **bevor** der Lauf S7 erreicht
(≈ 08.11. vormittags).

---

## 4a. Prüfung von a gegen unsere LLM-Regeln (Nutzer 05.11.: *„gehe vorher in unsere LLM Dokumente und regelwerke und prüfe ob dies der norm bzw unserem Ziel entspricht, wenn ja dann mit kurs“*)

Gelesen: CLAUDE.md (Ziel, vier Regeln) · [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) Ü1–Ü9 und §3a ·
[`Voranalyse_Dashboard_LLM_28_10.md`](Voranalyse_Dashboard_LLM_28_10.md) §2–§5 (P1–P9, „nicht empfohlen“) ·
[`Bilanz_LLM_Komponente_21_10.md`](Bilanz_LLM_Komponente_21_10.md) §2–§3 (elf Wege) · [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) §3–§4 ·
Memory N5-Ursachen (W1–W4) und *LLM-Rolle muss die Wette kennen* (Echo, R-R2).

| Regel | a (Kurs in die S7-Eingabe) | Urteil |
|---|---|---|
| §3a Ergebnisform: `eingepreist` „mit Beleg (Kursreaktion)“, Frage S7 „hat der Kurs schon reagiert?“ | erfüllt | ✔ spricht dafür |
| Ü2 Fakt und Bewertung getrennt · Regel 4 | die Kursreaktion ist ein Fakt der Gegenwart | ✔ |
| Ü8 dieselbe Form live und im Rückspiel | am NB stündlich für die REGEL0-Menge; Bestände ohne Binance „unbekannt“ in beiden | ✔ |
| Messnorm: Ertrag NACH dem Informationszeitpunkt | Kursreaktion endet T 00:00, Zielgröße beginnt T 01:00 | ✔ |
| **Ü5: jede Stufe bringt NEUE Information, „nicht dieselben Kurszahlen ein zweites Mal — genau daran ist Lagebild → Trader → Entscheider gescheitert“** | Das finale LLM bekommt den Kurs je Asset ohnehin (Datenbasis §3). Mit a ginge er **zweimal** hinein: einmal direkt und einmal versteckt in S7 | ✗ |
| **W1 (N5-Ursachen): kein LLM-Urteil über Zahlen** · Bilanz §3 · Dashboard §5 „nicht empfohlen: noch ein LLM-Urteil über dieselben Zahlen“ | Steht der Kurs in der Eingabe, folgt `wirkung` ihm leicht (N5 Ursache 1: Lehrbuch-Trendlogik) | ✗ Risiko, das genau die gescheiterten Wege wiederholt |
| R-R2 Echo | Die Kursreaktion nach einem Rückgang ist nahe an dem, was die REGEL0 auslöst (Kauf nach Rückgang): S7 spräche dann dieselbe Zahl in Worten noch einmal aus | ✗ |

**Ergebnis:** a erfüllt die Ergebnisform, **verstößt aber gegen Ü5 und W1**, also gegen die Regeln, die aus elf gescheiterten Wegen
entstanden sind. Die Kurs-Regel im Vergleichsarm würde den Verstoß zwar **messen**, ihn aber nicht vermeiden.

**Normgerecht ist eine vierte Form, d:** Der **Code** liefert die Kursreaktion als Fakt **neben** dem S7-Ergebnis, nicht in die
S7-Eingabe.
- Das S7-LLM liest nur, was **nicht** in den Kursen steht: die Meldung (I1, „LLM als Leser“, Dashboard §3). `wirkung` heißt dann
  „was die Meldung für das Asset bedeutet“. `eingepreist` setzt das S7-LLM auf „unbekannt“. Der Code hängt
  `kursreaktion` (seit der Meldung, gegen BTC, Zeitfenster, Quelle) an das abgelegte Ergebnis.
- **F3 ist damit beantwortet, als Fakt und ohne Urteil** (Ü2, P3). Die **Abwägung** „Meldung belastet, Kurs hat schon −10 % gegen
  BTC“ macht das **finale LLM**, das ohnehin beides bekommt. Dort entsteht die Verbindung **einmal**, nicht zweimal (Ü5).
- **Die Messung von S7 wird sauberer:** Sie prüft das reine Textverständnis. Die Kurs-Regel bleibt im Vergleichsarm als Auskunft:
  Trägt die Kursreaktion allein etwas, ist das ein Fakt-Befund für die Asset-Karte, kein LLM-Befund.
- **Umbau:** S7-Prompt anpassen (neue S7-SHA, **vor** dem ersten S7-Aufruf, keine Doppelaufrufe), Kursreaktion im Code je Asset und
  Stichtag (Rückspiel: Arbeitskopie; live: `stundenkurse`), Prüfpaket erweitern (kein Vorgriff).
- **Schema:** Das Feld `eingepreist` bleibt in allen Sichten gleich (§3a „dasselbe Schema für alle“). Bei S7 trägt es „unbekannt“ plus
  den Code-Fakt.

**Empfehlung jetzt: d statt a.** Damit wird die Frage „hat der Kurs schon reagiert?“ beantwortet, ohne die Regel zu brechen, an der
Lagebild → Trader → Entscheider gescheitert ist.

## 5. Gegenprüfung dieser Voranalyse

| Aussage | geprüft wie | Ergebnis |
|---|---|---|
| Kein LLM-Urteil gelesen | beide Skripte öffnen `gutachten.db` nicht; die Urteile im Grobtest sind künstlich (`g_lauf`, `g_asset`, `g_markt`) | ✔ |
| Zellen = Eingabe des Laufs | `zellen()` nutzt `sichten_gutachten.Quelle` und `ereignisse.am` wie `eingabe()` | ✔ (dieselbe Funktion) |
| Zielgröße ohne Vorgriff | σ mit `shift(1)` (nur Tage vor T); Kursreaktion endet bei T 00:00 (Schluss der Stunde 23:00 von T−1) | ✔ |
| Stunde = Beginn der Kerze | Schema `stundenkurse(stunde, close)` wie in Stufe 3 (`k.get(t0)` = Schluss der Einstiegsstunde) | ✔ Schluss der Stunde „00:00“ = Kurs um 01:00 |
| Asset-Ereignis verworfen, nicht schöngerechnet | gleiche Erzeuger, gleiche Saatlogik, Ergebnis 36,5 % offen ausgewiesen | ✔ |
| 200 Ziehungen reichen nicht für ein Urteil | Standardfehler ≈ 1,5 Pp; 6,5 % gegen Soll 5 ist nicht entschieden | ⚠ → Selbsttest 1.000 im Bau |
| S7-Urteile je Tag in der Probe | Probe 3: S7 an 3 Tagen 2 / 1 / 2 Assets | ✔ „2 je Tag“ ist der realistische Fall; 5 als Obergrenze |
| Termin S7 im Lauf | Plan: 5 × 352 = 1.760 Aufrufe vor S7; Start 05.11. 07:36, 98 Gutachten in 30 min (≈ 200/h); Topf heute 480 − 46 Probe, dann ≈ 480 je Tag ab 09:00 | 05.11. ≈ 434 · 06.11. ≈ 914 · 07.11. ≈ 1.394 · **08.11. ≈ 11:00** |

## 4b. Nutzeridee 05.11.: S7 bekommt nur das WORT (gestiegen / gefallen / unverändert), das finale LLM die Zahl — geprüft

Nutzer 05.11.: *„S7 bekommt keine Zahlen sondern nur Textinfo – gestiegen, gefallen, unverändert und das finale LLM bekommt den genauen Kurs in Zahlen?“* — Form **e**. Vorgabe dazu: *„die Kursreaktion muss so angeführt sein, dass diese zum Urteil passt“*.

**Gerechnet** (`Rechenkern_02_10/g7_s7_wort.py`, nur Kurse, kein LLM-Urteil): 9.419 Zellen, Reaktion seit der Meldung gegen BTC in üblichen Schwankungen (σ · √Alter).

| Grenze | unverändert | gefallen | gestiegen |
|---|---|---|---|
| ± 0,5 σ | 57,1 % | **27,9 %** | 15,0 % |
| ± 1,0 σ | 82,8 % | 10,4 % | 6,8 % |

Je Meldungstyp (± 0,5 σ) fällt `listing_spot` in 45 % (!), `monitoring` 40 %, `netz_upgrade` 34 %; das Wort ist zu 77 % dasselbe wie am Vortag.

**Befund zur Idee:**
1. Das Wort nimmt die **Genauigkeit** heraus, nicht die **Richtung** — und die Richtung ist genau der Kanal, über den N5 gescheitert ist (Trendlogik: Urteil folgt dem Kurs). Wo ein Wort steht, steht fast doppelt so oft „gefallen“ wie „gestiegen“ → Zug Richtung „belastet“.
2. Ü5 bleibt verletzt, nur gröber: dieselbe Kursinformation geht über S7 **und** direkt ins finale LLM.
3. Vorteil von e: S7 kann `eingepreist` selbst füllen (§3a). Unter d tut das das finale LLM mit der genauen Zahl — dort ist sie besser aufgehoben (ein „gefallen“ bei BTC ist etwas anderes als bei einem Kleinwert; der σ-Maßstab hilft, das Wort verliert ihn trotzdem).
4. **Ob e besser ist, sagt keine Überlegung, sondern nur die Messung** (Ü6 „mit und ohne messen“; *„eine Erklärung, die man messen kann, ist zu messen“*). Kosten: ein zweiter S7-Arm = 352 Aufrufe ≈ ¾ Tag Kontingent → S7 fertig ≈ 09.11. statt 08.11.

**„Passend zum Urteil“ angeführt (gilt für d und e gleich):** je S7-Asset-Zeile hängt der Code an — dasselbe Asset, dieselbe E-Nummer, Zeitfenster **ab Bekanntwerden der Meldung bis Stichtag**, Quelle, Kurs in %, gegen BTC in %, und in üblichen Tagesschwankungen. Beispiel:
`ARB · S7: belastet [E3 hack_exploit] · Kurs seit Meldung (34 h): −8,1 %, gegen BTC −6,4 % (= −1,3 übliche Schwankungen) · Quelle stundenkurse`

**Empfehlung:** **d als Hauptarm** (vorab registriert), **e als zweiter Arm gemessen**. Vorab festgelegt: e ersetzt d nur, wenn e trägt und d nicht, oder wenn die gepaarte Differenz e − d über ihrem eigenen Nullband liegt. Sonst bleibt d.

---

## 6. Bau 05.11.2026 — Nutzer: *„Ja, d + Wort-Arm“*

| # | Was | Wo | Stand |
|---|---|---|---|
| B5 | **Kursreaktion als Fakt**: je (Meldung, Asset) Kurs ab Schluss der Meldungsstunde bis T 00:00, gegen BTC (BTC selbst absolut), in üblichen Schwankungen (σ · √Alter, σ aus 60 T vor T), Wort mit Grenze ±0,5; `satz()` für das finale LLM | `agent/kursreaktion.py` (neu) | ✔ gegen die Voranalyse unabhängig nachgerechnet: 300 Zellen, größte Abweichung 7e−5 (Rundung) |
| B5 | **S7 = Form d**: Frage ohne „hat der Kurs schon reagiert“, `eingepreist` IMMER unbekannt (sonst als Formfehler gezählt), kein Kurs im Text; Kursfakt je E-Nummer und Asset in der Ablage (`ereignisse` → `kurs`). **S7w = Arm e**: Frage mit Kurs, je Ereigniszeile „Kurs seit Meldung (gegen BTC; BTC selbst absolut): ARB gefallen, …“, `eingepreist` je Asset | `agent/sichten_gutachten.py` | ✔ Prompt-SHA S7 `e028ae4a7b40`, S7w `3c54879f44ef`; **S1–S4/S8 byte-gleich** (laufender Lauf ohne Doppelaufruf) |
| B5 | Prüfpaket `SichtenGutachten` | `pruefe_pakete.py` | ✔ **20/20** (neu u. a.: S1–S4/S8-SHAs fest, S7 ohne Kurs im Text, S7w = S7 + genau das Wort, Kursfakt endet genau bei T, eine verdreifachte Zukunft ab T ändert nichts, S1–S4/S8 lesen nie einen Kurs) |
| B1–B3 | **Anlage**: Panel, t-Statistik, Nullwelt Asset-Zeit per FFT (gegen naive Schleife: Abweichung 2,7e−15), gepaarter Vergleich, Typ-Regel mit gleicher Rate, Kurs-Regel als Auskunft; `--messen` verweigert sich, solange S7 und S7w nicht vollständig sind | `Rechenkern_02_10/g7_s7_anlage.py` | ✔ gebaut · Selbsttest → §6.1 |
| B4 | Vorabfestlegung S7 | `Voranalyse_G7_Stufe1_04_11.md` §4.1 | ✔ geschrieben, Commit vor dem ersten S7-Aufruf (auf Ja) |
| — | Lauf mit dem neuen Code **neu angestoßen** 05.11. ≈ 11:50 (PID 1828), 2.328 offen von **2.464** | `data/_g7_stufe1_lauf2.txt` | ✔ setzt ohne Doppelaufruf fort |

**Nebenbefund Laufzeit (05.11.):** Der Lauf wurde stündlich langsamer (72 → 26 → 19 → 13 je Stunde). Ursache **gemessen**, nicht vermutet: die Schnittstelle antwortet mit **503 „This model is currently experiencing high demand“** — Serverlast bei Google, **nicht** unser Kontingent (ein Kleinaufruf ging durch, der echte Aufruf bekam 503). Der Lauf wartet und fragt erneut, verliert nichts. Das Protokoll zählt seit dem Neustart die Wartegründe mit (`Warten {…}`). ⚠️ Folge: der Termin „S7 ≈ 08.11.“ hält nicht, solange die Last bleibt; bei ≈ 15–20 je Stunde liegt S7 eher **nach dem 10.11.** Ein Modellwechsel ist **keine** Abhilfe (Ü8, Kontamination, ein Modell je Lauf).

### 6.1 Selbsttest der Anlage (1.000 Ziehungen, `g7_s7_anlage.txt`) — kein LLM-Urteil gelesen

| Prüfung | Ergebnis | Soll |
|---|---|---|
| FFT-Bahn gegen naive Schleife | Abweichung 2,7e−15 | gleich |
| Fehlalarm Hauptstatistik: G-Lauf 2 / 5 je Tag · G-Asset 5 % · G-Markt L 3 / 10 | **5,9 · 6,3 · 4,5 · 6,0 · 4,4 %** | ≤ 6,5 % Toleranz → **keine Eichung, Band = 95. Perzentil** |
| Fehlalarm gepaarter Vergleich (gleiche Information): mit Wirkung · ohne · G-Typ | 6,2 · 5,0 · 4,6 % | ≤ 6,5 % |
| Auflösung Hauptstatistik, 2 Urteile/Tag: 0,1 · 0,2 · 0,3 σ | 33 · **79** · 95 % | (grob war 42 · 82 · 98) |
| Auflösung Hauptstatistik, 5 Urteile/Tag | 64 · 98 · 100 % | |
| Auflösung gepaarter Vergleich, Wirkung 0,2 σ, B zu 30 / 50 / 100 % neu gelost | 26 · 42 · 58 % | |

⚠️ **Lesart des gepaarten Vergleichs:** er ist **schwach**. Selbst wenn ein Arm 0,2 σ trägt und der andere gar nichts, findet er den Unterschied nur in 58 %. Der Weg „e ersetzt d über die Differenz“ wird also selten greifen; realistisch entscheidet die Holm-Zeile (§4.1: e trägt über P97,5, d nicht). Das ist **vorab** so festgehalten, damit es hinterher niemand als Ausrede liest.

**Auskunft auf den echten Zielgrößen (Regeln ohne LLM, nie hochgestuft):**

| Regel | t | Grenze | Rang | Urteil |
|---|---|---|---|---|
| Typ-Regel voll (3.188 stützt / 2.293 belastet) | +0,24 | +5,47 | 0,37 | trägt nicht |
| **Kurs-Regel Fortsetzung** (das Wort als Urteil) | −2,93 | +4,11 | 0,14 | trägt nicht |
| Kurs-Regel Gegenrichtung | +2,93 | +4,69 | 0,86 | trägt nicht |

→ Das **Wort allein** sagt über die nächsten 3 Tage **nichts Trennbares** (Rang 0,86 in Gegenrichtung, innerhalb des Bands). Bringt S7w trotzdem mehr als S7, kommt es aus dem **Zusammenspiel** von Meldung und Wort, nicht aus dem Wort — genau das misst der Arm. Die Typ-Regel trägt ebenfalls nicht: der Vergleichsmaßstab für S7 liegt niedrig.

### 6.2 Probe 3 Tage, nur S7 und S7w (05.11., `data/_g7/gutachten_probe.db`) — nur Form und Treue, kein Kurs danach

| | S7 (d) | S7w (e) |
|---|---|---|
| lesbar / Formfehler / Treue-Beanstandungen | 3/3 · 0 · 0 | 3/3 · 0 · 0 |
| `eingepreist` | 3 × unbekannt (wie verlangt), kein Feld je Asset | teilweise / teilweise / teilweise; je Asset ja · teilweise |
| Assets mit Urteil | 1 · 3 · 3 | 1 · 1 · 2 |

**Ein Befund für Stufe 2 (Auskunft, nicht hier entschieden):** S7w schreibt am 12.02. bei BTC „teilweise eingepreist — der Kurs hat reagiert“, obwohl das gezeigte Wort **unverändert** war. Prüfer v2 sieht das nicht (er prüft Zahlen, Schlüssel und Belege, keine Wörter). Weil Wort und Antwort abgelegt sind, wird in Stufe 2 als **Wort-Treue** gezählt: gestiegen/gefallen → ja/teilweise, unverändert → nein. Drei Tage sind dafür keine Zahl.

STAR am 25.10. zeigt, warum das Wort am σ hängt: −6,7 % gegen BTC ist bei diesem Wert **unverändert** (kleiner als eine halbe übliche Schwankung).
