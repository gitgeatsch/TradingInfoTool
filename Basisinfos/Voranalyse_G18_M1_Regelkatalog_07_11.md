# Voranalyse G18 M1 — Regel-Katalog gegen die Drift (07.11.2026)

> Zurück zum laufenden Plan: [`Gesamtplan.md`](Gesamtplan.md)

Nutzer 07.11.: *„Ja, M1 Voranalyse“* · Grundlage: E-170 (F-B, F-C), [`Voranalyse_G18_Gesamtkonzept_06_11.md`](Voranalyse_G18_Gesamtkonzept_06_11.md) §5,
[`Vorabfestlegung_G18_M0_Erfolgsmessung_07_11.md`](Vorabfestlegung_G18_M0_Erfolgsmessung_07_11.md) §6.

**Bis hier wurde kein Ergebnis angesehen.** Gezählt wurden nur Zustände (Phasen, Beständigkeit) und Datenmengen, nie gegen Kurse.

## 0. Das Ergebnis in sechs Sätzen

1. Gemessen wird gegen die **Drift**: REGEL0-Einstieg minus Mittel der Vergleichsmenge zur selben Stunde. Das folgt aus M0, wo das
   Plus im Oktober das Plus des Markts war.
2. Ein **Marktzustand** gilt für alle Assets gleich. Er kann den Vorsprung nur über eine **Wechselwirkung** ändern: Wählt REGEL0 in
   dieser Lage schlechter oder besser als der Durchschnitt? Daraus folgt die Regel „in Lage X auslassen“ oder „in Lage X eine andere
   Regel“.
3. **Langsame** Zustände (200-Tage-Abstände, Zinsen, NFCI, Dollar, DVOL …) haben im Betriebszeitraum 1–13 Phasen. Das ist zu wenig,
   sie sind **nicht messbar** und bleiben Information. Damit ist F-B (E-170) bestätigt.
4. **Schnelle** Zustände (Funding, Coinbase-Prämie, offene Positionen) haben genug Phasen, aber **nur auf einem längeren Zeitraum**
   als den 11 Betriebsmonaten.
5. Der zweite Teil des Katalogs sind **Ereignisse je Asset** (A1). Das ist die einzige Information, die wirklich ein Asset vom anderen
   unterscheidet.
6. **Offen ist eine Entscheidung:** auf welcher Grundgesamtheit gemessen wird (§5).

## 1. Die Frage und der Maßstab

| | Festlegung | Grund |
|---|---|---|
| Einheit | **Tag** (alle REGEL0-Einstiege eines Tages sehen denselben Markt) | M0, §23.64 |
| Zielgröße | **Vorsprung** = 24-h-Ertrag des Einstiegs − Mittel der 24-h-Erträge der Vergleichsmenge ab derselben Stunde, brutto | M0 §6, Memory *Nullpunkt ist die Drift*, Regel 2 |
| Zustand | Wert des **Vortags** (T − 1) für Einstiege am Tag T | Ein Tageswert an einer Stunde von T ist Vorgriff (Memory *Tageswert an Stundenanker*) |
| Form | **Rangkorrelation** Zustand ↔ Tages-Vorsprung, **zweiseitig**, ein Test je Kandidat. Die Schalter-Form („in Lage X auslassen“) wird erst **nach** einem Befund gebaut | Für die Wechselwirkung gibt es keine fachliche Richtung. Eine Schwelle vorab zu wählen wäre eine zweite Stellschraube |
| Nullwelt | Kreisverschiebung der Zustandsreihe, volle Bahn (wie `g7_messanlage`) | erhält die Beständigkeit des Zustands |
| Mindestmaß | ≥ 20 Blöcke à 15 T | messnorm |
| Mehrfachtests | Holm über alle Kandidaten der Gruppe A, getrennt Gruppe B | |
| „trägt“ | nur mit Band, je Tag, Geltungsbereich und **zweitem Weg** (andere Epoche), sonst „Hinweis“ | Memory *TRÄGT braucht Band + zweiten Weg* |

## 2. Befunde — geprüft, ohne Blick auf ein Ergebnis

### M1-1 Langsame Zustände sind nicht messbar

Phasen im oberen Fünftel, Dez. 2025 – Okt. 2026 (335 Tage):

| Zustand | Phasen | | Zustand | Phasen |
|---|---|---|---|---|
| BTC / ETH (Abstand 200 T) | 2 / 2 | | S&P 500 / Nasdaq 100 | 9 / 8 |
| Zinsen 2 J / Realzins / Kurve | 2 / 7 / 5 | | NFCI / Baa | 4 / 7 |
| Netto-Liquidität / M2 | 5 / 1 | | Dollar / Gold / Öl / Kupfer | 10 / 8 / 5 / 13 |
| DVOL BTC / ETH | 7 / 11 | | Basis BTC / ETH | 8 / 4 |
| Stablecoins / Breite TOP50 | 6 / 11 | | VIX / MOVE / SOXX | 10 / 7 / 8 |

Die wirksame Stichprobe ist die Zahl der **Phasen**, nicht der Tage (Befund 2.599). Selbst über 2023–2026 bleiben NFCI 3,
ETH 13 und BTC 17 Phasen. → **Information, nicht Regel.** Das deckt sich mit E-133 (Marktfilter nicht entscheidbar) und E-170 F-B.

### M1-2 Schnelle Zustände sind messbar, aber nicht auf 11 Monaten

| Zustand | Phasen Dez. 25 – Okt. 26 | Phasen 2025-01 – 2026-10 | Phasen 2024-01 – 2026-08 | Beständigkeit (1 Tag) |
|---|---|---|---|---|
| Funding ETH | 34 | 56 | 32 | 0,60–0,65 |
| Funding BTC | 26 | 50 | 31 | 0,74–0,75 |
| Coinbase-Prämie BTC / ETH | 23 / 20 | 46 / 41 | 70 / 68 | 0,86–0,87 |
| Offene Positionen BTC / ETH | 19 / 15 | 29 / 32 | 46 / 37 | 0,89–0,90 |
| GDELT-Töne | 27–42 | 80 | — | 0,31–0,67 |

Auf 11 Monaten (22 Blöcke) reicht das knapp für Funding und kaum für den Rest. Auf **2024-01 bis 2026-08** (≈ 65 Blöcke) reicht
es für alle. → Die Messung braucht den **längeren** Zeitraum, siehe §5.

⚠️ **Funding hat über 2024–2026 weniger Phasen als über 2025–2026** (31 gegen 50). Das hohe Funding ballt sich 2024. Ein Zustand, der
an einer Epoche hängt, misst sonst die **Epoche** statt der Lage. Deshalb gilt: Die Rangkorrelation wird **je Epoche** gerechnet
(2024 / 2025–26), und ein Befund braucht **beide** mit gleichem Vorzeichen (der zweite Weg).

### M1-3 Die Befunde aus Stufe 0c sind keine Bestätigungsgrundlage

Stufe 0c maß, ob ein Zustand die **Marktrichtung** (BTC, Breite) vorhersagt. M1 fragt etwas anderes: ob REGEL0 in dieser Lage **besser
oder schlechter als der Markt** wählt. Die 0c-Befunde sind dafür **neue Hypothesen** ohne Richtung, keine Reproduktion. Darum wird
zweiseitig gemessen. Eine Marktrichtung als Filter wäre wieder E-133 (*den Markt messen*) und ist hier ausgeschlossen.

### M1-4 GDELT-Töne nicht in den Katalog

Sie sind schnell genug, aber **live nicht verlässlich** (K-GD-1: K1 verfehlt). Ein Befund wäre nicht anwendbar (Ü8). Sie kommen nur
hinein, wenn der Rohdaten-Weg gebaut wird ([`Voranalyse_GDELT_Rohdaten_07_11.md`](Voranalyse_GDELT_Rohdaten_07_11.md)).

### M1-5 E-138 (Tagesbreite) bleibt vorwärts

E-170 F-C: nur auf Daten ab 25.10. Der erste Blick (M0 D2) zeigt das Gegenteil. Das bleibt eine **Vorwärtszeile** (M7), keine
Rückwärtsmessung, denn rückwärts ist die Hypothese aus den Daten selbst entstanden.

### M1-6 Ereignisse je Asset sind der eigentliche Beitrag je Asset

A1 hat 25.561 Ereignisse ab 2023 mit Typ, dazu kommen die Binance-Ankündigungen ab 2023. Ein Ereignis unterscheidet **ein Asset vom
anderen**. Das verlangt die Nutzervorgabe vom 25.09. (*„Beiträge, die für einzelne Assets genutzt werden“*).
- Frage: Haben REGEL0-Einstiege mit einem Ereignis eines Typs in den 72 h davor einen anderen Vorsprung als die übrigen am selben Tag?
- Abgrenzung zu S7 (G7): S7 misst das **LLM-Urteil** über Ereignisse auf **allen** Asset-Tagen. M1-B misst **Typ-Regeln** auf den
  **REGEL0-Einstiegen**. Die S7-Messung ist vorab festgelegt und wird davon nicht berührt.
- Die Typen werden zu Gruppen zusammengefasst (stützend / belastend / neutral nach S7-4), damit es wenige Tests bleiben.

### M1-7 Die Grundgesamtheit entscheidet, wofür ein Befund gilt

| Menge | Einstiege | Zeitraum | Assets | gilt für |
|---|---|---|---|---|
| **Referenzmenge** `kern48jbz_einstiege_bestand.csv` | 10.732 | 2024-01 – 2026-08 | 127 | die registrierte REGEL0-Messung (E-139, Menge *bestand*) |
| **Betriebsmenge** (G7 §10) | 20.069 | 2025-12 – 2026-10 | bis 653 | was am NB läuft |

Die Mengen sind verschieden: Die Zusatzwerte der Betriebsmenge schwanken stärker (G7 §10.3). Nach Memory *Grundgesamtheit ist keine
Stellschraube* gilt ein Befund **nur** für die Menge, auf der er gemessen wurde.

## 3. Der Katalog — Entwurf

| Gruppe | Kandidat | Tests |
|---|---|---|
| **A Tageszustand (Vortag)** | Funding BTC · Funding ETH · Coinbase-Prämie BTC · Coinbase-Prämie ETH · Offene Positionen BTC · Offene Positionen ETH | 6, Holm |
| **B Ereignis je Asset (72 h davor)** | stützende Typen · belastende Typen · irgendein Ereignis | 3, Holm |
| nur Information | alle langsamen Zustände (M1-1), GDELT (M1-4) | — |
| vorwärts (M7) | E-138 Tagesbreite (M1-5) | — |

## 4. Der Weg

| Schritt | Was | Kosten |
|---|---|---|
| **M2 Selbsttest** | Nullwelten mit der **echten** Beständigkeit je Zustand. Auflösung als Kurve (gepflanzter Vorsprung 0,1–0,5 Pp). Für B: Ballung je Asset und Tag. **Vor** dem ersten Blick | Desktop, ohne LLM, ≈ 1 h |
| **M3 Messung** | einmal, nach der Vorabfestlegung (§3 + Entscheidung §5), Epochen 2024 / 2025–26 getrennt | ≈ 1 h |
| danach | trägt etwas → Schalter-Form bauen und in die Kette (M6), vorwärts als Herausforderer (M7). Trägt nichts → das Ergebnis geht in den Scheideweg Ende November | — |

## 5. Zur Abstimmung — eine Frage: Auf welcher Menge wird gemessen?

| | Weg | Was passiert | Folge |
|---|---|---|---|
| **1** | **Referenzmenge 2024-01 – 2026-08 als Hauptmessung**, Betriebsmenge Dez. 25 – Okt. 26 als Auskunft daneben | Alle neun Kandidaten haben genug Phasen. Zwei Epochen (2024 / 2025–26) geben den zweiten Weg | Ein Befund gilt zunächst für die 127 Werte der Referenz. Vor dem Betrieb muss er auf der Betriebsmenge vorwärts bestätigt werden (M7). Bis dahin wäre er ein Kandidat, keine Regel |
| 2 | **nur Betriebsmenge** Dez. 25 – Okt. 26 | genau das, was läuft | Die meisten Kandidaten fallen unter das Mindestmaß (M1-2). Für Funding ETH reicht es knapp, ohne zweiten Weg. Das Ergebnis wäre fast sicher „kein Befund“, und zwar wegen der Länge, nicht wegen der Sache |

**Empfehlung 1.** Nur dort sind die Daten lang genug, um überhaupt etwas zu sehen. Die Einschränkung (gilt erst für die Referenzmenge)
ist ehrlich ausgewiesen und wird vorwärts geschlossen.

**Danach, ohne weitere Frage:** Vorabfestlegung §3/§5 festschreiben, M2 Selbsttest, M3 Messung, Bericht.

## 6. Entschieden 07.11.2026 (E-173): Weg 1, Referenzmenge — Vorabfestlegung, VOR dem ersten Blick

Nutzer 07.11.: *„1 Referenzmenge“* und *„immer prüfen und gegenprüfen dann doku - bei jedem Schritt“*.

**Prüfung der Daten vor der Festlegung (nur gezählt):**
- Einstiege: `kern48jbz_einstiege_bestand.csv`, 10.732 (2024: 2.324 · 2025: 4.715 · 2026: 3.693), 127 Werte. Die Spalte `stunde` zählt die
  Stunden seit 2020-01-01. Die Einstiegsstunde ist geprüft gegen `b_einstiege_betrieb.csv` (3/3 gleich) und das Jahr (0 Abweichungen).
- **Ereignisse sind über die Zeit nicht gleich dicht.** Nachrichten (A1) mit Asset: 2025 1.959, 2026 11.386, davon Dez. 2025 – Mai 2026
  je ≈ 2.000 im Monat, vorher ≈ 100. Binance mit Asset: 554 / 1.004 / 655, gleichmäßig. → Gruppe B nimmt **nur Binance und Upbit**.
  Mit den Nachrichten würde B die **Datenlage** messen statt der Ereignisse. Nachrichten bleiben bei S7 (G7).

**Festgelegt:**

| | |
|---|---|
| Einstieg | Schluss der Stunde `stunde` (bekannt ab `stunde` + 1 h), 24-h-Ertrag = Schluss `stunde` + 24 / Schluss `stunde` − 1 · Kurse Messbasis `stundenkurse.db`, dann `stundenkurse_alle.db` (erste Datei gewinnt, wie `regel0_messstand`) |
| Drift | Mittel der 24-h-Erträge **aller 127 Werte** mit Kurs ab derselben Stunde (≥ 20 Werte), wie M0 D3 |
| Vorsprung | Einstieg − Drift, brutto · **Tageswert** = Mittel der Einstiege des Tages (UTC-Tag der Einstiegsstunde) |
| **A** Zustand | `rang` des Vortags T − 1 aus `zustaende_taeglich` · Statistik: Spearman (Zustand, Tages-Vorsprung) · 6 Kandidaten: `S1.funding.BTC`, `S1.funding.ETH`, `S1.coinbase_praemie.BTC`, `S1.coinbase_praemie.ETH`, `S1.oi.BTC`, `S1.oi.ETH` |
| **B** Ereignis | Marke je Einstieg: Binance-/Upbit-Ereignis des Assets an den **Tagen T − 3 … T − 1** (vor dem Einstiegstag, kein Vorgriff). Gruppen nach S7-4: **stützend** (`listing_*`, `airdrop`, `netz_upgrade`, `etf_fonds`), **belastend** (`delisting_*`, `monitoring`, `depeg_aussetzung`, `hack_exploit`), **irgendein** Ereignis mit Asset · Statistik: Mittel Vorsprung (mit Marke) − Mittel (ohne) |
| Nullwelt | A: Kreisverschiebung der Zustandsreihe über die Einstiegstage der Epoche, volle Bahn · B: Ereignisreihe **jedes** Assets um dasselbe k Tage im Kreis, volle Bahn (wie S7) |
| Epochen | **2024** und **2025-01 – 2026-08**, je eigene Nullwelt |
| Befund | in **beiden** Epochen außerhalb des Bands mit **gleichem Vorzeichen**. p des Kandidaten = größeres der zwei p. **Holm** über A (6) und getrennt über B (3), α = 0,05 zweiseitig. Ohne Befund: „trägt nicht“ oder „nicht trennbar“, je nach Auflösung |
| Mindestmaß | je Epoche ≥ 20 Blöcke à 15 T mit Einstiegen, bei B ≥ 20 Blöcke mit markierten Einstiegen, sonst KEIN BEFUND |
| Selbsttest M2 | A: Zustände als AR(1) mit der **echten** Beständigkeit gegen den echten Tages-Vorsprung; B: Ereignisse je Asset zufällig verschoben. Fehlalarm der ganzen Regel ≤ 5 %, Auflösung als Kurve (gepflanzt 0,1–0,5 Pp). **Vor** dem ersten Blick |
| Auskunft, nie hochgestuft | Betriebsmenge Dez. 25 – Okt. 26 (G7 §10) für A · je Epoche die Einzelwerte · B mit Nachrichten nur Dez. 25 – Mai 26 |
| Gegenprüfung | vor dem Messen: Werkzeug und Festlegung durch eine **unabhängige** Prüfung (ohne Ergebnis), danach Messung, danach Gegenprobe der Zahlen auf zweitem Rechenweg |

Werkzeug: `Rechenkern_02_10/g18_m1_regelkatalog.py` (`--pruefen`, `--selbsttest`, `--messen`) → `g18_m1_regelkatalog*.txt`.

### 6.1 Nachtrag nach der Prüfung — 07.11.2026, VOR dem ersten Blick (`g18_m1_regelkatalog_pruefen.txt`)

**Geprüft (nur Zählungen):** 10.732 Einstiege, alle mit 24-h-Ertrag und Drift. Die Drift beruht auf im Median 123 Werten je Stunde, mindestens 73.
Gegenprobe des 24-h-Ertrags direkt aus der Kursdatei: 5/5 gleich. Ereignisse Binance/Upbit mit Asset: 5.629, davon 1.378 in der Referenzmenge.

**Zwei Fehler der Festlegung §6, gefunden vor jedem Ergebnis:**

| | gezählt | Folge für §6 |
|---|---|---|
| Epoche 2024 | **174** Tage mit Einstieg, **17 Blöcke** (< 20) | Die Regel „Befund nur in **beiden** Epochen“ hätte **nie** erfüllt werden können. Die Messung wäre „kein Befund“ allein durch ihre Bauart gewesen |
| B je Epoche | 2024: stützend 25 / belastend 6 / irgendein 57 markierte Einstiege (10 / 4 / 13 Blöcke) · 2025–26: 36 / 28 / 131 (22 / 17 / 37 Blöcke) | Je Epoche fast überall unter dem Mindestmaß |

**Korrektur (ersetzt die Zeilen „Epochen“ und „Befund“ in §6):**
- **Hauptmessung gepoolt** 2024-01 – 2026-08 (671 Einstiegstage). Die Nullwelt (Kreisverschiebung über die ganze Bahn) erhält die
  langsamen Strukturen des Zustands, auch dessen Ballung in 2024.
- **Befund** = außerhalb des Bands (zweiseitig) nach **Holm** (A 6, B 3), Mindestmaß ≥ 20 Blöcke (bei B: Blöcke mit Marke).
- **Epochen je einzeln als Auskunft.** Gleichheit wird nicht verlangt (Memory *Epochen: kein gleiches Ergebnis erwarten*).
- **Zweiter Weg = vorwärts** auf der Betriebsmenge (M7, wie in E-173 ohnehin verlangt). Bis dahin heißt ein Befund **„Hinweis“**.
- Selbsttest M2 auf der gepoolten Bahn, mit dieser Regel.

### 6.2 Nachtrag nach der unabhängigen Gegenprüfung — 07.11.2026, VOR dem ersten Blick

Gegenprüfung durch einen getrennten Prüfer, der nur gelesen und gezählt hat, ohne Ergebnis. Jeden Punkt habe ich selbst nachgeprüft,
bevor ich ihn übernommen habe.

| # | Befund der Gegenprüfung | selbst nachgeprüft | Änderung |
|---|---|---|---|
| 1 | Die Cache-Zeile T kennt nur, was **vor T 00:00** bekannt war. Mit „Vortag T − 1“ wurde der Stand **T − 2** gelesen, also ein Tag Trennschärfe verschenkt | `zustaende.stand_am`: `bekannt_ab <= T` (T ohne Uhrzeit, Textvergleich → nur bis T 00:00) und `s.index < T` | Zustand = **Zeile T** (Stand T 00:00). Einstiege liegen frühestens T 01:00 → kein Vorgriff |
| 2 | **Lücke im Asset-Leser:** `ereignisse.binance_assets` erkennt Kürzel erst ab 2 Zeichen (S, A, W, T fehlen) und schließt BTC/ETH als Kurswährung aus | Regex `{2,15}` und `BA.QUOTE` im Code; 464 Meldungen mit Klammer-Kürzel bei leerer Liste, davon 40 in der Referenzmenge (meist BTC/ETH-Wallet-Wartung, dazu Sonic, Vaulta, Wormhole) | Im **Werkzeug** werden bei leerer Liste die Klammer-Kürzel aus dem Titel ergänzt: 1.378 → 1.418 Meldungen in der Referenzmenge. Den Leser selbst ändere ich **nicht**, weil die eingefrorene S7-Eingabe daran hängt → eigener offener Punkt |
| 3 | Docstring sagte noch „Befund nur in BEIDEN Epochen“ | ja | berichtigt |
| H1 | AR(1) bildet die Beständigkeit über Monate nicht nach | ja | Selbsttest A mit **Ersatzreihen aus der echten Zustandsreihe** (zufällige Phase, Werteverteilung erhalten); Auflösung je Kandidat bei **seiner** Beständigkeit |
| H2 | Selbsttest B mit eigenem k je Asset zerstört die Ballung über Assets | ja | zusätzlich ein Erzeuger mit **gemeinsamem** k |
| H3 | B: rohe Differenz bei schwankender Zahl der Marken | ja | B-Statistik = **Welch-t** |

Damit gepoolt: B stützend 67 / belastend 34 / irgendein 195 markierte Einstiege in 36 / 21 / 52 Blöcken. „Belastend“ liegt knapp über
dem Mindestmaß.

### 6.3 Nachtrag nach dem Selbsttest — 07.11.2026, VOR dem ersten Blick

Erster Selbsttest auf dem korrigierten Werkzeug (`3a3d0a4c30a576f0`): **B bestanden**, **A nicht bestanden**.
- **A:** Mit der Kreisverschiebung allein liegt der Fehlalarm je Kandidat bei 5,1–6,9 %. Funding BTC ist mit 6,9 % über der Toleranz
  6,5 %. Die Familie mit Holm liegt bei 4,7 %, also erfüllt. Ursache: Die echten Zustandsreihen haben ein langes Gedächtnis.
  Ersatzreihen mit demselben Spektrum zeigen, dass die Kreisverschiebung allein für den einzelnen Kandidaten leicht zu großzügig ist.
- **Eichung, wie bei S7 (§4.1, Band P96,5):** Für A entscheidet das **geeichte p**, also der Anteil von 1.000 Ersatzreihen desselben
  Zustands, deren p kleiner oder gleich dem beobachteten ist. Das macht die Regel strenger, nie lockerer. Das rohe p steht als Auskunft
  daneben.
- Der Selbsttest prüft nun genau diese geeichte Regel auf frischen Ersatzreihen, je Kandidat und als Familie.
- **Auflösung, ehrlich:** Der Tages-Vorsprung streut um **3,4 Pp**. Ein Unterschied von **0,5 Pp** zwischen oberem und unterem Fünftel
  wird nur in 50–58 % der Fälle gefunden, 0,3 Pp in 18–19 %. Ohne Befund heißt das Urteil daher **„nicht trennbar unter ≈ 0,5 Pp“**,
  nicht „trägt nicht“. B findet 1,0 Pp in 46–100 % der Fälle, je nach Gruppe.

### 6.4 Nachtrag — Selbsttest der geeichten Regel, 07.11.2026, VOR dem ersten Blick

Lauf `3252e13193654552` mit 300 Ziehungen: geeicht 3,7–5,0 % je Kandidat, **Offene Positionen BTC 8,7 %** (Grenze 7,5 %), Familie 4,0 %.
B bestanden (5,0–7,0 %). **Nachgeprüft mit 1.000 Ziehungen:** oi.BTC **5,1 %**, Vergleich funding.ETH 5,1 % → die 8,7 % waren Zufall
der zu kleinen Zahl. Der Selbsttest läuft deshalb mit 1.000 Ziehungen für die geeichte Regel. Sonst ändert sich nichts.

### 6.5 Nachtrag — Prüfkriterium des Selbsttests, 07.11.2026, VOR dem ersten Blick

Lauf `3e34c5710684e7c1` (1.000 Ziehungen): geeicht 4,3 / 4,9 / **6,8** / 4,5 / **7,0** / 5,0 %, Familie 5,7 % (Grenze 6,4 %). B bestanden.
**Das Werkzeug verlangte „jeder Kandidat ≤ 5 % + 2 Standardfehler“.** Das ist selbst ein Mehrfachtest: Selbst wenn alle sechs exakt 5 %
hätten, reißt einer die Grenze in ≈ 13 % der Läufe (1 − 0,977⁶). §6 verlangt dagegen den Fehlalarm der **ganzen Regel**. Geprüft wird
nun genau das:
- die Familie mit Holm: 5,7 % bei einer Grenze von 6,4 %;
- das Mittel über alle 6.000 Einzelziehungen: 5,4 % bei einer Grenze von 5,56 %.

Die Einzelwerte stehen als Auskunft daneben. Die Zufallszahlen bleiben gleich (feste Saat), also auch die Zahlen. Es ändert sich nur
die Prüfzeile.

## 7. Ergebnis M3 — 07.11.2026 (`g18_m1_regelkatalog.txt`, Werkzeug `397c0cd495ef13f1`, Selbsttest bestanden)

Gepoolt 2024-01 – 2026-08 · 10.732 Einstiege an 671 Tagen (57 Blöcke) · Vorsprung gegen die Drift, brutto, je Tag.

| | Kandidat | Maß | Band 2,5/97,5 | p (A geeicht) | Urteil |
|---|---|---|---|---|---|
| A | Funding BTC | ρ −0,062 | −0,075 / +0,081 | 0,120 | trägt nicht |
| A | Funding ETH | ρ −0,050 | −0,076 / +0,072 | 0,239 | trägt nicht |
| A | Coinbase-Prämie BTC | ρ +0,011 | −0,074 / +0,070 | 0,787 | trägt nicht |
| A | Coinbase-Prämie ETH | ρ −0,005 | −0,074 / +0,070 | 0,849 | trägt nicht |
| A | Offene Positionen BTC | ρ +0,011 | −0,071 / +0,083 | 0,799 | trägt nicht |
| A | Offene Positionen ETH | ρ −0,057 | −0,067 / +0,074 | 0,090 | trägt nicht |
| B | stützend (67 markiert, 36 Bl.) | t +1,84 | −2,35 / +1,63 | **0,028** | trägt nicht (Holm verlangt ≤ 0,017) |
| B | belastend (34, 21 Bl.) | t −0,44 | −2,48 / +1,75 | 0,720 | trägt nicht |
| B | irgendein (195, 52 Bl.) | t +0,81 | −2,15 / +1,76 | 0,452 | trägt nicht |

**Gegenprobe auf zweitem Weg** (Kurse je Einstieg direkt aus der Datei, Drift je Stunde neu gemittelt, `scipy.spearmanr` und
`scipy.ttest_ind` statt FFT-Bahn und eigener Rechnung): alle 6 ρ und das t von „stützend“ **gleich auf 4 Stellen**.

**Lesart, ohne mehr hineinzulegen:**
- **A: Kein schneller Marktzustand verändert, wie gut REGEL0 gegen den Markt wählt.** Die Auflösung lag bei ≈ 0,5 Pp (oberes gegen
  unteres Fünftel, Fundquote ≈ 50 %). Kleinere Wirkungen sind damit **nicht ausgeschlossen**, sondern nicht trennbar. Für eine Regel
  „in Lage X REGEL0 auslassen“ gibt es keine Grundlage.
- **B stützend** liegt vor der Korrektur über dem Band (p 0,028), hält Holm aber nicht. Getragen wird es von 2024 (+3,0 Pp bei
  26 Einstiegen); 2025–26 sind es +0,3 Pp bei 41. Das ist **kein Befund**, höchstens eine Vorwärtszeile.
- **Für die Kernaussage E-169** („mehrere Regeln je Lage“) heißt das: Aus den Tageszuständen ohne LLM entsteht **keine** Lage-Regel für
  den Einstieg. Offen bleiben die Ereignisse als **LLM-Urteil** (S7, mit Nachrichten), das finale LLM (G7 Stufe 3) und das **Wie** der
  Handlung (M5: Führung, Ausstieg).
- Die Auskunft auf der Betriebsmenge (§6) ist **nicht** gelaufen. Sie kann ein „trägt nicht“ auf der Referenzmenge nicht umkehren
  (R-R11) und wird nur nachgeholt, wenn ein Kandidat vorwärts verfolgt wird.
