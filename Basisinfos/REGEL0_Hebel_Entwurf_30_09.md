# REGEL0 — die festgeschriebene Ausgangslage des Hebel-Neubaus — ✔ FESTGESCHRIEBEN 01.10.2026

> ⭐ **Stand: FESTGESCHRIEBEN 01.10.2026** (Nutzer: *„Ja, REGEL0 festschreiben, prüfen und gegenprüfen“*, E-36), mit **J** (2.698) und der bestätigten
> **Schwellenwahl** (2.699). Im Code: `hebel_neubau.REGEL0`. Die Wache vergleicht die Referenzzahlen mit den Belegdateien.
> Der Dateiname mit *Entwurf* ist historisch und bleibt, damit die Verweise gelten. Entstanden als Entwurf am 30.09.2026.
> ⭐ **Fassung 0.1 seit 02.10.2026** (2.708, Abschnitt 13): dieselbe Regel in **kausaler** Rechenform. Die Einstiege sind in 3 von 4 Mengen und in der Betriebsreferenz **bitgleich**.

**Nutzer 30.09.2026:** *„Offenbar haben wir einen stabilen Stand bzw. eine Ausgangslage, welche in eine REGEL0 mit allen
korrekten Parametern festgeschrieben werden muss, und mit allen uns zur Verfügung stehenden Mitteln das Regelwerk optimieren und
ausreizen."* Dazu: *„A und B sind Optionen, die ohnehin sinnvoll sind. C, D, E sehe ich aktuell gar nicht als Option für unseren Umbau."*

> **Zweck:** REGEL0 ist der **Nullstand**. Jede weitere Optimierung wird **gegen REGEL0** gemessen (R-R11: erst REGEL0 bitgleich
> reproduzieren, dann ändern). Die Parameter stammen aus den Befunden 2.688–2.699.

---

## 1. Grundgesamtheit und Daten

| | REGEL0 | Befund |
|---|---|---|
| Messbasis | Binance-Stundenkurse und Terminmarkt, **mit den eingestellten Paaren** (`--menge unverzerrt`) | 2.668/2.669 |
| Zeitraum | Wahl **2024**, Bestätigung einmal **2025-01..2026-08**, 2022 nur Gegenprobe | E-21 |
| Urteil | ≥ 3 von 4 Mengen (bestand, unverzerrt:1–3). Laufen sie auseinander, gilt **unverzerrt** | E-30 |
| Grundgesamtheit | Betrieb und Messung brauchen **dieselbe**, weil die v̂-Skala an der Menge hängt | E-31, CLAUDE.md |

## 2. Bewertung 1 — der Einstieg (Rolle A, *ob*)

| Parameter | REGEL0 | Befund |
|---|---|---|
| Beitrag | **rsi**: rollierendes Kurvenmodell (Form b, 12 Stufen, `rsi_s` und `rsi_s24`), **monatlich** neu geschätzt, Training ab 2023-01 bis Monatsbeginn −24 h, nur **reife** Stunden. ⚠️ Im Betrieb ist das ein Monatstraining am Notebook (Bauaufgabe, Schritt 7) | 2.683/2.684, 2.688 |
| **eigenes Normal** (J) | aus der vorhandenen Historie ab **240 h**, geschrumpft an Marktmitte und τ² der reifen Assets. **Mindesthistorie der Regel: 10 Tage** | 2.698 |
| Dämpfung | Kreuzvalidierung über 4 Zeitblöcke, Raster `GITTER_NEU` (20 … 2.000.000) | M1-1 ⚠️ grob, siehe B |
| Vorsprung | v̂ = expit(logit(QSh) + Beitrag) − QSh, **QSh** = geschrumpftes Normal (stündlich). **Fassung 0.1:** Marktmitte, τ² und Schrumpfung aus dem **Vormonat** (kausal). ⚠️ τ² ist in 31 von 33 Monaten **null**: QSh ist damit fast immer die **Marktmitte** des Monats | 2.684, **2.708** |
| **Ereignis** | **Ersteintritt**: erste Stunde mit **v̂ ≥ +0,035** | 2.687/2.688 (per Regel auf 2024) |
| **Ruhe davor** | **48 h** unter der Schwelle (≥ 40 gültige Stunden) | 2.691/2.692/2.694 |
| Einstieg | **1 h** nach dem Signal, nicht in den ersten 24 h eines Monats | 2.688 |
| **Prüfzeitpunkt** (Betrieb, 02.10.) | **jede volle Stunde** nach Kerzenschluss (UTC), **alle** Assets. Eine Änderung der Lage sieht das System also spätestens nach einer Stunde | Nutzer 02.10. |
| **Cooldown** (Betrieb, 02.10.) | **kein eigener.** Die Ruhe 48 h wirkt **je Asset**. Gemessen: Zwei Signale desselben Assets liegen mindestens **49 h** auseinander, im Median **6,8 Tage**. Damit gibt es höchstens **eine** Position je Asset (Haltedauer 24 h < Ruhe). Andere Assets können in jeder Stunde signalisieren | gemessen 02.10. |
| Zielgröße (Maß) | q5: +5 % vor −5 % binnen 24 h, gegen das geschrumpfte Normal | K4 |
| **REGEL1-Kandidat** (Nutzer 02.10.) | **Fortsetzung**: ein eigener Einstiegstyp für Assets, die nach dem Signal stark weiterlaufen. Heute ist ein zweiter Einstieg erst nach der Ruhe möglich | offen |
| **nicht** Teil von REGEL0 | Stärke (ordnet nicht, 2.691) · Wucht als Einstieg (Bewegung, 2.693) · Tempo, Tiefe, Ruhe 72 h (2.695) · Kern-Short (Spur, 2.696) · K_IG-Kontext (Auskunft, 2.697) | |

## 3. Bewertung 2 — der Hebel (Rolle C, *wie viel*)

| Parameter | REGEL0 | Befund |
|---|---|---|
| Risikomodell | **ATR zum Einstieg**, rollierend geschätzt, die Liquidationsgefahr je Stufe | 2.667/2.681 |
| Stufen | 2x / 3x / 5x. Gewählt wird die **höchste** Stufe mit geschätzter Liquidationswahrscheinlichkeit binnen H **≤ Grenze**, sonst kein Handel | K6, 2.681 |
| **Grenze** | **2 %** (per Regel auf 2024) | 2.690 |
| Kurs | **Markpreis**, Bitpanda-Liquidationsformel mit m = 0,09 | 2.679 |
| Prüfung auf den Einstiegen | vorsichtig, kein Aufschlag | 2.689 |

## 4. Erfolgsmessung (nicht Bewertung) — die Referenz für jede Optimierung

| | REGEL0 | Befund |
|---|---|---|
| Geometrie | **24 h** halten, **ohne** Ziel, **ohne** Stop | 2.690 (per Regel auf 2024) |
| Kosten | 0,30 % + 0,18 %/Tag auf den **Positionswert**, +1 % bei Liquidation (am Bitpanda-Buch geprüft) | 2.690 |
| Konto | f = 1 % je Handel, log-Wachstum | 2.690 |
| Pflichtprüfungen | Nullwelt, je Jahr, Spot-Vergleich, mit/ohne 10./11.10.2025, **Spiegel** bei Potential-Maßen | E-29 |

## 5. Die Referenzzahlen — REGEL0 muss sie bitgleich treffen (R-R11)

**✔ GÜLTIG (mit J und BTC, E-37), von der Wache gegen `Basisinfos/BTC_01_10/sim__<m>.txt` geprüft:**

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| Einstiege 2024–26 (Export) | 10.000 | 10.429 | 9.761 | 10.049 |
| Hebelkonto 2025–26 (log) | +0,2708 | −0,4887 | −0,4592 | −0,4065 |
| Rohvorteil je Handel 2025–26 | +0,583 % | +0,325 % | +0,331 % | +0,345 % |

Aufruf: `messe_losfahren.py --kern --ruhe 48 --junge --mit-btc --export 0.035` und `messe_k6_hebelstufe.py --kurs mark --mit-btc --einstiege kern48jb_einstiege_<m>.csv --simulation 24,ohne,0.02`.

*Ohne BTC (mit J, 2.698), die übrigen Handel sind bitgleich zu oben:*

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| Einstiege 2024–26 (Export) | 9.905 | 10.337 | 9.670 | 9.956 |
| Hebelkonto 2025–26 (log) | +0,2634 | −0,4877 | −0,4543 | −0,4058 |
| Rohvorteil je Handel 2025–26 | +0,583 % | +0,324 % | +0,331 % | +0,343 % |

Aufruf: `messe_losfahren.py --kern --ruhe 48 --junge --export 0.035` und `messe_k6_hebelstufe.py --kurs mark --einstiege kern48j_einstiege_<m>.csv --simulation 24,ohne,0.02`.

*Zum Vergleich — die Zahlen **ohne J** (Stand 30.09., nicht mehr gültig als Referenz):*

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| Einstiege 2024 / 2025–26 | 1.486 / 6.328 | – / 7.121 | – / 6.463 | – / 6.782 |
| Chance Dq 2024 / 2025–26 | +0,1615 / +0,1039 | – / +0,0774 | – / +0,0697 | – / +0,0781 |
| Hebelkonto 2025–26 (log) | +0,2038 | −0,4662 | −0,4166 | −0,3824 |
| Rohvorteil je Handel | +0,573 % | +0,294 % | +0,311 % | +0,309 % |

(damaliger Aufruf ohne `--junge`, `kern48_einstiege_<m>.csv`)

## 6. Bekannte Schwächen von REGEL0 — der Optimierungsauftrag

| | Schwäche | Weg |
|---|---|---|
| 1 | Vorteil je Handel (+0,29..+0,31 %) **unter den Kosten** (0,48 %) | **A** Positionsführung (W4): nachgezogener Stop oder Ziel, die Wucht als Bewegungsgröße (Rolle B) · ⛔ **versucht (2.702):** nachgezogener Stop von Hand nicht bestätigt (0/4). ⭐ 2.703 Teil 0: ohne Kosten 4/4 positiv, die Kosten sind der größte Posten |
| 2 | Das Signalangebot **springt**, weil die Dämpfungswahl im groben Raster kippt | **B** Kern stabilisieren (M1-3) · ⛔ **versucht (2.703):** feinere Dämpfung springt weniger, kostet aber Chance. Das Springen ist kein Verlusttreiber, F0 bleibt (E-39) |
| 4 | ✔ **BEHOBEN (2.698, J):** ~~Showstopper~~ **Mindesthistorie 12 Monate** für das eigene Normal (`JAHR_H = 8760`, im Code `normal()`). Junge Assets bekommen im **ersten Jahr kein Signal**, obwohl rsi, Ruhe und ATR nur Tage brauchen. Auf der Hebel-Liste sind **12 von 28** Assets jung (TAO, ONDO, RENDER, MORPHO, KAIA, S, W, BIO, TURBO, IO, VIRTUAL, KAITO). Nutzer 30.09.: *„Das System braucht keine Historie, um bei der Prüfung den Einstieg zu bewerten, oder?“* (vgl. 2.610) | **J** junge Assets: das Normal anfangs aus dem **Markt**, mit wachsender eigener Historie überblendet (die Schrumpfung gibt es schon), gemessen gegen REGEL0 |
| 3 | im Gegenwind **stumpf** (Modell flach) | innerhalb von A und B zu lösen, zum Beispiel ob die Stabilisierung das Regime anders abbildet |

➤ **Ablauf der Optimierung (Vorschlag):** Jede Änderung wird **einzeln** gegen REGEL0 gemessen, mit Voranalyse, Wahl 2024 und einmaliger
Bestätigung. Was trägt, wird **REGEL1** usw., und jede Stufe wird mit ihren Referenzzahlen festgeschrieben.

---

## 7. Zurückgestellt (Nutzer 30.09.: *„aktuell gar nicht als Option für unseren Umbau"*)

C Vorwärtstest ab 2026-09 (die Regel K_IG < 1 bleibt eingefroren, aber kein laufender Prüfauftrag) · D neue Datenquellen · E Börse/Kosten.


---

## 8. ✔ BEHOBEN (2.698) — war: SHOWSTOPPER vor der Festschreibung, die Mindesthistorie (Nutzer 30.09.)

**Nutzer:** *„Die erforderliche Mindesthistorie ist eigentlich ein Showstopper und keine Schwäche, finde ich, und war so nicht geplant
und gewünscht, vor allem wenn man unsere Datenlage berücksichtigt."*

➤ **Folge:** REGEL0 wird **erst nach der Behebung** festgeschrieben. Die 12-Monats-Bedingung ist kein *korrekter Parameter* (E-33),
denn sie widerspricht der Grundanforderung *„muss auch bei nur EINEM Asset funktionieren“* (2.608) und *„10 Tage Historie, nicht
Jahre“* (2.610).

**Wo sie sitzt (Code):** `normal()` verlangt `st - st[0] >= JAHR_H` (8.760 h) und mehr als 1.000 Stunden. Ohne das gibt es kein eigenes
Normal, also kein QSh, kein v̂, kein Signal.

**Lösungsweg — auf dem Bestehenden, ohne neue Zahl:**

| | |
|---|---|
| Schrumpfung (besteht) | je Monat QSh = Marktmitte + B × (eigenes Normal − Marktmitte), mit B = τ² / (τ² + Rauschen). Je weniger eigene Ereignisse, desto mehr Rauschen und desto näher an der **Marktmitte** |
| **Änderung** | Das eigene Normal wird aus der **vorhandenen** Historie gerechnet (höchstens 12 Monate). Das Rauschen wird aus der **tatsächlichen** Zahl eigener Ereignisse bestimmt. Ohne eigene Historie ist QSh = Marktmitte. Ein junges Asset startet so auf dem **Marktnormal** und wächst mit seiner Historie hinein |
| Mindesthistorie danach | nur noch, was das **Signal** braucht: rsi-Monatsabstand (10 Tage), ATR (etwa 14 Tage). Abgeleitet, nicht gewählt |
| **R-R11** | Marktmitte, τ² und das rsi-Modell werden weiter **nur aus den reifen Assets** geschätzt. Für Assets mit ≥ 12 Monaten ändert sich damit **nichts**, und die Referenzzahlen der REGEL0 bleiben bitgleich. Junge Assets kommen **zusätzlich** hinzu |
| Messung | Kern-Einstiege junger Assets in ihrem ersten Jahr: Chance gegen ihr Normal, Spiegel, Nullwelt, je Jahr, Rohvorteil in der Simulation. **Kriterium:** nicht schlechter als die reifen Assets (Dq > 0 in beiden Jahren, über der Nullwelt) |


---

## 9. ✔ J ist Teil der REGEL0 (Befund 2.698)

| Parameter | REGEL0 mit J |
|---|---|
| **eigenes Normal** | aus der **vorhandenen** Historie (höchstens 12 Monate), ab **240 h**. Geschrumpft an derselben Marktmitte und τ², das Rauschen aus Rate × min(365, Tage der Historie). Ohne eigene Historie: Marktmitte |
| Training des rsi-Modells, Marktmitte, τ² | weiter **nur aus reifen** Stunden (≥ 12 Monate), damit bitgleich |
| **Mindesthistorie der Regel** | **10 Tage** (rsi-Monatsabstand, 240 h) |
| Wirkung | +18–21 % Einstiege auf 72–74 zusätzlichen Assets, tragen in 4/4 Mengen |

**Referenzzahlen mit J** (ersetzen Abschnitt 5 nach der Festschreibung):

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| Einstiege 2024–26 | 9.905 | 10.337 | 9.670 | 9.956 |
| Rohvorteil je Handel 2025–26 | +0,583 % | +0,324 % | +0,331 % | +0,343 % |
| Hebelkonto 2025–26 (log) | +0,2634 | −0,4877 | −0,4543 | −0,4058 |

Aufruf: `messe_losfahren.py --kern --ruhe 48 --junge --export 0.035` und `messe_k6_hebelstufe.py --kurs mark --einstiege kern48j_einstiege_<m>.csv --simulation 24,ohne,0.02`.
✔ Schritt 2 erledigt (2.699): Die Schwellenwahl auf der vollständigen 2024-Menge ergibt wieder **s = +0,035**, in der REGEL0-Form mit dem Abstand +0,088 gegen +0,066. **Die REGEL0 kann festgeschrieben werden** (Nutzer-Ja).


---

## 10b. BTC (2.701) — ✔ AUFGENOMMEN (Nutzer 01.10., E-37)

Mit `--mit-btc` wird BTC zusätzlich ausgewertet, ohne die REGEL0 für die anderen zu ändern (bitgleich). Mit etwa 30 Signalen je Jahr ist BTC **nicht nachweisbar**, aber **unschädlich** (Konto um null, keine Liquidation). ✔ **Nutzer 01.10.: *„Ja, BTC aufnehmen.“*** BTC ist handelbar, mit dem Vermerk *nicht nachgewiesen, unschädlich*. Die Referenz in Abschnitt 5 gilt jetzt mit BTC.

## 10a. Auskunft — REGEL0 auf der Hebel-Liste des Nutzers (2.700)

Auf den 25 gehandelten Assets der Liste: Hebelkonto **+0,2063 (×1,23)**, beide Jahre positiv, Rohvorteil **+0,87 %** gegen 0,48 % Kosten, Rückgang 0,083. Die Auswahl trägt: Zufallslisten liegen bei +0,59 %. ⚠️ Rückschau-Vorbehalt, die Liste ist die heutige. Das ist **keine** neue Referenz, die REGEL0-Referenz bleibt Abschnitt 5.

## 10. ✔ FESTSCHREIBUNG (01.10.2026, E-36)

| Prüfung vor der Festschreibung | Ergebnis |
|---|---|
| Showstopper Mindesthistorie | ✔ behoben mit J (2.698), 4/4 Mengen |
| Schwellenwahl auf der vollständigen 2024-Menge | ✔ wieder s = +0,035 (2.699), Abstand +0,088 gegen +0,066 |
| R-R11 der Referenzzahlen | ✔ die Zahlen in Abschnitt 5 = Belegdateien (Wache `regel0_gegen_belege`, 0 Abweichungen), mit Gegenprobe |
| Code | ✔ `hebel_neubau.REGEL0` mit allen Parametern, Aufruf und Referenz |

➤ **Ab jetzt:** Jede Optimierung wird eine **REGEL1 …** mit Voranalyse, Vorab-Festlegung und der Betriebsprüfung B1–B9 (E-35). Sie reproduziert zuerst REGEL0
(Referenzzahlen Abschnitt 5) und wird nur mit Nutzer-Ja festgeschrieben. Nächste Schritte nach Plan: **4** Betriebsprüfung am Notebook (Befundaufnahme) ·
**5** Messung auf der Hebel-Liste · **6** REGEL1..n (A, B, R, L, Käuferanteil).


## 11. Die REGEL0 auf der vollständigen Datenbasis (O11, 01.10.2026, E-40) — Befunde 2.705–2.707

| | |
|---|---|
| **Geltungsbereich** | jedes Krypto-Asset, das Binance stündlich führt (Spot oder Futures, je die längere Historie). Messbasis bleiben die **116** Assets in `data/stundenkurse.db` |
| **Neue Assets** | werden **bewertet, nicht trainiert** (`--zusatz`): Modell, Marktmitte und ATR-Training kommen aus der Messbasis. Die REGEL0-Referenz oben bleibt **bitgleich** (R-R11 zeilengleich, Konto der übrigen = Referenz in 4/4) |
| **Nachweis** | Die REGEL0 trägt für die 11 neu bewerteten Assets in 4/4 Mengen (2.706), wirtschaftlich wie die breite Menge |
| **Zuordnung** | `Basisinfos/symbol_zuordnung.csv`: nur Ausnahmen (CANTON → CC, CAT → 1000CAT). **Gesperrt** sind LIT, NEIRO, ONE, QUICK, ZK (anderer Coin unter gleichem Kürzel, 2.707) |
| **Ohne Markpreis** | 126 reine Spot-Assets (z. B. XNO): Sie bekommen Signale, aber **keine** Hebelstufe |
| **Signalbilanz** | 25–45 Signale je Asset und Jahr. 40 von 60 Assets aus Watchlist, Bestand und Hebel-Liste bekommen Signale. Ohne Binance bleiben AIOZ, SUPRA, VSN, XDC |
| **Optimierungsversuche** | A (2.702), B (2.703), L (2.704) haben die REGEL0 **nicht** verbessert. Sie bleibt unverändert |


## 12. Betrieb — Positionsgröße (E-44, 02.10.2026; nicht Teil der Bewertung)

Die REGEL0 liefert **Signal** und **Hebelstufe**. Die **Positionsgröße** ist eine Betriebsfestlegung, die der Nutzer anpasst. Startwerte stehen in `Basisinfos/regel0_betrieb.yaml`:
Positionswert 1.500 € je Trade, Einsatz = Positionswert / Stufe (5x 300 €, 3x 500 €, 2x 750 €), begrenzt auf 300–800 €, Richtwert 4 gleichzeitig **ohne Sperre**.
Die Erfolgsmessung oben (Einsatz 1 % des Kontos) bleibt die **Referenz** für jede REGELn.

## 13. Fassung 0.1 — die Schrumpfung kausal (2.708, 02.10.2026)

**Anlass (Schritt 7, S7-2, B-1):** Die Messung nahm Marktmitte, τ² und Schrumpfungsfaktor je Asset aus **allen** Gitterstunden des **laufenden** Monats. Eine Stunde
am 10. nutzte also Werte vom 11. bis zum 31. Das ist ein Vorgriff, und im Betrieb ist es nicht nachbaubar.

**Fassung 0.1:** Diese Größen kommen aus dem **Vormonat**. Ein Asset ohne Vormonat (jung, BTC, neu) nimmt seine Gitterstunden des laufenden Monats **bis zur
Stunde t**. Aufruf mit `--normal kausal`, im Code `hebel_neubau.REGEL0["fassung_0_1"]`.

**Teil 0** (Regel vorab, E-45; Beleg `Basisinfos/Teil0_02_10/ergebnis_teil0.txt`):

| Menge | Einstiege gleich | Rohvorteil je Handel | Konto |
|---|---|---|---|
| bestand | **bitgleich** (10.000) | unverändert +0,583 % | unverändert |
| unverzerrt:1 · :2 | **bitgleich** | unverändert | unverändert |
| unverzerrt:3 | 98,7 % (161 Abweichungen, **alle im Januar 2026**, 85 Assets) | **+0,350 %** statt +0,345 % | −0,384 statt −0,407 |
| **Betriebsreferenz** (mit den Zusatz-Assets deiner Listen, 127 Assets) | **bitgleich** (10.732) | — | — |

→ 4 von 4 Mengen erfüllen die Regel. **Fassung 0.1 gilt**, und der Betrieb rechnet sie. Die Referenzzahlen in Abschnitt 5 gelten für bestand, unverzerrt:1 und :2
unverändert. unverzerrt:3 hat in Fassung 0.1 die Referenz 9.958 Einstiege, Konto −0,3840, Rohvorteil +0,350 %. Die Signalbilanz je Asset ist **unverändert**.

**Warum so klein:** v̂ ist der Vorsprung **gegen** das Normal. Eine Verschiebung des Normals hebt sich bei q um 0,47 fast vollständig auf: |ΔQSh| im Median 0,005,
|Δv̂| im Median 0,0000075.

⭐⭐ **Nebenbefund:** τ² ist in **31 von 33 Monaten null**, in bestand wie in unverzerrt:3 und in beiden Fassungen. Das geschrumpfte Normal ist damit in der Bewertung
fast immer die **Marktmitte** des Monats. Das eigene Normal eines Assets wirkt nur noch über den Offset im **Training**. Das passt zu 2.683 (*das Normal ist meist
Rauschen*). Die Beschreibung *Vorsprung gegen die eigene Phase* trifft für die Bewertung also nicht zu: Es ist ein Vorsprung gegen die **Marktmitte**.

⚠️ Offen und **nicht geklärt:** Warum in unverzerrt:3 gerade der Januar 2026 die Schwelle anders sieht (674 Stunden).
