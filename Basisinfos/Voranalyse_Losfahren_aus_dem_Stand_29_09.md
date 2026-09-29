# Voranalyse — Losfahren aus dem Stand: die Anfahr-Kurve und die Lage auf stehenden Ankern (29.09.2026)

**Nutzer:** *„ja, Voranalyse schreiben — prüfen und gegenprüfen, abstimmen, wenn Bedarf besteht."* Dazu die Analogie
(ausdrücklich *kein Gesetz*): *„Auto steht noch, wann fahren wir los? — Sweet Spot (Kurve oder Schwelle) — das Auto
hat sich in Bewegung gesetzt, nicht von 0 auf 200, sondern 0 auf 20 (Auslöser, geht?)."*

> **Urteil in einer Zeile:** Der **Kern** ist die **Anfahr-Kurve** — trägt die Fortsetzung (rsi) am stärksten, wenn
> die Bewegung **gerade erst** begonnen hat? Ein früherer Hinweis ist stark (E2g: +0,316 nach Fall gegen +0,025 nach
> starkem Anstieg), aber **ungeprüft**. Die **Lage auf stehenden Ankern** ist zweitrangig: sie ist für funding schon
> weitgehend beantwortet (klein, vor allem Markt).

---

## 1. Was schon gemessen ist — und was davon folgt

| Befund | Frage | Ergebnis | Grenze |
|---|---|---|---|
| **2.650** | sagen Kursmerkmale die Bewegung **vorher**? (Karenz) | bei k ≥ 3 h **null** von 11 — sie begleiten | Ereignis-Lift, alle Anker |
| **2.651/2.663** | Terminmarkt mit Karenz | Haltequote 0,29–0,74, **kein Vorlauf** | mit Vorgriff (funding) gerechnet, dann korrigiert |
| **2.657** | Squeeze-Familie (hohe Vola + wenige Longs) | **hält 2024 nicht** | Episoden, +20/−10 %, 120 h |
| **2.665 · E2g Teil A** | Altersachse | funding 12 h alt hält **85 %** — **Lage vorher**; Käuferanteil und momentum begleiten | Bezug *Asset im selben Monat* |
| **2.665 · E2g Teil B** | ⭐ **Schichtung nach der 24-h-Vorbewegung** | **momentum oben: nach Fall +0,316 (1.386) · Mitte +0,003 · nach starkem Anstieg +0,025**; funding tief in S1–S4 +0,03..+0,04, nach starkem Anstieg −0,006; funding hoch wird mit der Vorbewegung schlechter (S5 −0,064) | **keine** Such-/Prüf-Trennung; kleine Fallzahl; anderer Bezug |
| **2.673** | funding in Markt und Eigen geteilt | Asset-Anteil trägt **nicht**, Marktanteil **nicht nachweisbar** (Auflösung gröber als 0,04) | Wirkungskurven, alle Anker |
| **2.675** | funding/konten marktweit am Rand | nur in der **Suche** | Prüfzeit im Marktrauschen |
| **2.682/2.683** | die Lage neben rsi | kommt nicht an — **rsi verdeckt die Lage** | Kombination, alle Anker |

➤ **Folgerung:**
- Für **funding** ist die Stand-Frage **schon gestellt**: Lage vorher, klein, vor allem Markt.
- **Neu und vielversprechend** ist die **Anfahr-Kurve**. E2g Teil B zeigt, dass *momentum oben* nach einem Fall rund **zwölfmal** so viel bringt wie nach starkem Anstieg. Das ist genau das Nutzerbild *0 auf 20* — aber auf gesehenen Daten, ohne Trennung, mit dem strengen Monatsbezug.
- Für **konten_verh** und **oi_aenderung** gibt es **keine** Stand-Schichtung.

---

## 2. Teil 1 (Kern) — die Anfahr-Kurve

**Frage:** Wo auf der „Tachonadel" trägt die Fortsetzung am meisten — **Stand, Anfahren oder Fahrt**?

| | |
|---|---|
| **Auswahl** | rsi allein (Rolle A *während*), oberstes Zehntel des Beitrags, **Grenze aus dem Training** (Betriebsform) — wie 2.683 |
| **Tachonadel** | bisheriger Anstieg der letzten **24 h in eigener ATR** (A4, `vor24 / ATR`): Klassen **< −1 · −1..0 · 0..0,5 · 0,5..1 · 1..2 · > 2 ATR** |
| **zweite Nadel (Auskunft)** | Anstieg der letzten **120 h** in ATR (`vor120`): *schon lange unterwegs?* |
| **Maß** | Dq der Auswahl je Klasse, gegen das **geschrumpfte** Normal (2.684) |
| **Zielgröße** | q5 (+5 vor −5 %, 24 h); Auskunft: +5 vor −5 % binnen **72 h** (Anfahren braucht womöglich länger) |
| **Form** | eine **Kurve** über die Klassen — keine Schwelle festlegen (E-18) |

## 3. Teil 2 — die Lage auf stehenden Ankern

| | |
|---|---|
| **R-R11 zuerst** | `messe_e2g_fortsetzung.py` **unverändert** laufen lassen: Ausgabe **bitgleich** zu `Ergebnis_E2g_Fortsetzung_27_09.txt` — sonst nicht weiter |
| **stehend** | \|Anstieg 24 h\| < 0,5 ATR (nur über den **Kurs** definiert, nicht über rsi — sonst wäre die rsi-Gegenprobe zirkulär) |
| **Beiträge** | funding (Vortag), konten_verh, oi_aenderung — **für sich**, je mit den Fenstern 0/24/48 h (K5 neu), eigenes Zehntel |
| **Markt/Eigen** | jeder Beitrag zusätzlich geteilt in Markt (Median aller Assets zur Stunde) und Eigen (Asset − Markt); Markt mit **gemeinsamer** Nullwelt (2.673) |
| **Gegenprobe** | rsi auf denselben stehenden Ankern |

---

## 4. Die Kriterien — vorab

| # | Bedingung | bei Nein |
|---|---|---|
| **L0** | R-R11: E2g bitgleich | nicht weiter |
| **L1** | **Tor** Teil 1: gepflanzt +0,04 in der **frühen** Klasse der rsi-Auswahl (rsi verschoben) — die Differenz früh − spät muss in ≥ 4 von 5 über dem Nullband liegen (das Tor trifft genau die Messgröße von L2) · Tor Teil 2: gepflanzt +0,04 auf dem obersten Zehntel eines Lage-Beitrags auf stehenden Ankern, ≥ 4 von 5 | kein Urteil |
| **L2** | ⭐ **Sweet Spot:** Dq der rsi-Auswahl **früh** (Anstieg ≤ 0,5 ATR, einschließlich negativ) minus **spät** (> 2 ATR) über dem Nullband (rsi verschoben je Asset, 40 Ziehungen, dieselben Klassen), fest **und** rollierend, in ≥ 3 von 4 Mengen | die Anfahr-Phase ist nicht besser als die Fahrt |
| **L3** | **Zeit:** die frühe Klasse > 0 in jedem Jahr 2024/2025/2026 (Betriebsform) und 2022 (Moment-Bezug) | nicht zeitstabil |
| **L4** | **je Asset:** ≥ 60 % der Assets (≥ 30 Auswahlanker in der frühen Klasse) mit Dq > 0 | Klumpen |
| **L5** | Teil 2: ein Lage-Beitrag (**Bestes-von-3**) auf stehenden Ankern über dem Nullband, fest und rollierend, in ≥ 3 von 4 | Lage vorher trägt auch auf stehenden Ankern nicht |
| **L6** | Teil 2: trägt es im **Eigen**-Anteil? | nur Markt → Rolle **Kontext**, nicht A (Regel *nicht den Markt messen*) |
| **L7** | Auskunft: Anteil der Signale je Klasse — *wie viele Einstiege blieben, wenn nur früh?* · die 72-h-Zielgröße · die 120-h-Nadel · rsi auf stehenden Ankern | – |

⚠️ **Mehrfachtesten:** Teil 1 hat **eine** vorab benannte Differenz (früh − spät); die übrigen Klassen sind Kurve, kein
Urteil. Teil 2 Bestes-von-3.
⚠️ **Dieselbe Prüfzeit** wie alle Messungen seit 26.09. — ein *trägt* bleibt Kandidat bis zur Simulation und den
Monaten ab 2026-09 (Z6).

---

## 5. Zur Abstimmung (P1–P8)

| # | Punkt | Empfehlung | Warum |
|---|---|---|---|
| **P1** | Reihenfolge | **Teil 1 zuerst**, Teil 2 danach im selben Werkzeug | Teil 1 hat den stärksten Hinweis (E2g Teil B) und beantwortet direkt, **wann** wir einsteigen |
| **P2** | Tachonadel | 24-h-Anstieg in eigener ATR, sechs Klassen; 120 h als Auskunft | ATR-Einheit = eigenes Tempo des Assets (2.667); die Klassen umfassen *Tal* (negativ) bis *Fahrt* |
| **P3** | früh / spät | früh ≤ 0,5 ATR, spät > 2 ATR — **vorab** | E2g: S5 (starker Anstieg) trug fast nichts; der K5-Werkzeugtest: > 1 ATR negativ |
| **P4** | Bezug | geschrumpftes Normal | 2.683/2.684 |
| **P5** | stehend (Teil 2) | \|Anstieg 24 h\| < 0,5 ATR, nur über den Kurs | rsi-Gegenprobe bleibt aussagekräftig |
| **P6** | Markt/Eigen (Teil 2) | geteilt, Markt mit gemeinsamer Nullwelt | 2.673; Nutzerregel *Beiträge je Asset* |
| **P7** | Zielgröße | q5 (24 h) als Urteil, 72 h als Auskunft | K4; Anfahren braucht womöglich länger |
| **P8** | Werkzeug | `messe_losfahren.py`, Aufbereitung aus der K5-Folge (R-R11 für rsi allein bitgleich zu 2.680); vorab committet | reproduzierbar |

---

## 6. Prüfung und Gegenprüfung dieser Voranalyse

| Prüfung | Ergebnis |
|---|---|
| schon gemessen? | **teilweise** — Abschnitt 1; neu sind: die Anfahr-Kurve mit Trennung, Bezug, Nullwelt und Tor; konten/oi auf stehenden Ankern; Markt/Eigen dort |
| Widerspruch zu einer Nutzerentscheidung? | nein — Rollen (A während / vorher), Achsen als Gewichte (die Kurve ist eine Achse, kein Blocker), Black Swans nur Störfaktor |
| OPTIMUM | Teil 1 misst **Anfahren**, nicht die Fahrt — der Nutzer hat das Anfahren (0 auf 20) als Optimum-Nähe beschrieben; Teil 2 misst den Stand |
| Vorgriff | Anstieg 24 h aus Schlusskursen bis zur Ankerstunde; funding als Vortag; Gegenprobe 1 h älter |
| Zirkularität | *stehend* ist über den Kurs definiert, nicht über rsi |
| Fallzahl | die frühe Klasse ist kleiner (E2g S1: 1.386) — Klassen mit < 200 Auswahlankern zählen nicht |
| Was folgt NICHT | kein Betrieb; die Hebelstufe bleibt Sache der ATR (Rolle C) |

---

## 7. Umfang

Werkzeug bauen und vorab committen · R-R11 E2g (einige Minuten) · Werkzeugtest · Tor · vier Mengen — nacheinander,
geschätzt 3–4 Stunden.

---

## 8. ✔ ABGESTIMMT (29.09.2026) — P1 bis P8 wie empfohlen

**Nutzer:** *„ja, P1 bis P8 wie empfohlen, bauen und messen, prüfen und gegenprüfen. Nur Hinweis: Ich kann deiner
Hypothese bzw. deinem Ansatz folgen — ob dies fachlich und technisch passt, musst du bestimmen, und wenn wir u. U.
auf Probleme stoßen oder die Annahmen nicht zutreffen, müssen wir vorsichtig nachjustieren und die Probleme lösen."*

➤ Festgehalten: Ein Nachjustieren **nach** einem Ergebnis ist eine **neue** Vorabfestlegung (mit Begründung, vor dem
nächsten Lauf committet) — nie ein stilles Anpassen der Kriterien an das Ergebnis.

---

## 9. ⚠️ NEUE VORABFESTLEGUNG nach dem Werkzeugtest (29.09.2026) — spät = > 1 ATR statt > 2 ATR

**Anlass (Struktur, nicht Ergebnis):** Der Werkzeugtest (`Losfahren_29_09/probe__bestand.txt`, R-R11 rsi allein
+0,0808 bitgleich, L0 E2g bitgleich) zeigt die Tachonadel in der Prüfzeit so verteilt:

| < −1 | −1..0 | 0..0,5 | 0,5..1 | 1..2 | > 2 |
|---|---|---|---|---|---|
| 5 % | 48 % | 29 % | 14 % | 5 % | **0 %** |

Die rsi-Auswahl hat in „> 2 ATR“ nur **150** Anker — unter der eigenen Mindestzahl von 200 (Abschnitt 4). **L2 wäre
damit nicht auswertbar.** Ursache: die ATR ist ein **Tagesmaß**; ein Anstieg von 2 Tages-ATR binnen 24 h ist
selten. Meine Annahme in P3 war falsch skaliert — die Schicht S5 aus E2g (+3,12 % in 24 h) entspricht etwa
**> 0,5 ATR**, nicht > 2.

| | vorher | jetzt |
|---|---|---|
| früh | ≤ 0,5 ATR | **unverändert** ≤ 0,5 ATR (50 % der Auswahl) |
| spät | > 2 ATR | **> 1 ATR** (rund 18 % der Auswahl — die höchste Grenze mit genügend Ankern) |
| alles andere | | **unverändert** (Klassen der Kurve, Kriterien L1–L7, Nullwelt, Tor) |

⚠️ **Offen ausgewiesen:** Die **feste Teilung** der Menge `bestand` ist im Werkzeugtest bereits voll gerechnet
(nur Ziehungen und Monate waren verkürzt) — ihre Kurve ist also **gesehen**. Sie **steigt** mit der Nadel
(früh +0,057 gegen 1..2 ATR +0,123). Die neue Grenze begünstigt die Hypothese daher **nicht**, sie macht L2 nur
auswertbar. Die übrigen drei Mengen und alle rollierenden Werte sind ungesehen.

---

## 10. ⚠️ NEUE VORABFESTLEGUNG nach dem Tor (29.09.2026) — Tor als LEITER, Urteil nur oberhalb der Auflösung

**Anlass:** Beide Tore sind an +0,04 **nicht bestanden** (`Losfahren_29_09/tor__bestand.txt`):

| | Nullwelt | gefunden bei +0,04 |
|---|---|---|
| Teil 1 (früh − spät) | Mittel −0,063, Streuung 0,019, P90 −0,040 | **2 von 5** (+0,02: 1 von 5) |
| Teil 2 (Bestes-von-3) | Mittel +0,006, P90 +0,016 | **3 von 5** |

➤ Nach Abschnitt 4 heißt das: **kein Urteil** zu L2 und L5 **aus diesem Tor**. Die vier Mengen laufen weiter, ihre
Werte sind vorerst nur **Auskunft**.

**Warum nicht einfach weiter?** Ein Tor, das nicht besteht, sagt nur: *+0,04 ist unter der Auflösung dieser
Anlage.* Ob der Effekt, den wir suchen, **größer** ist (der E2g-Hinweis war rund +0,29), bleibt offen. Das beantwortet
die **Leiter**, die der Messstandard ohnehin vorsieht (*gepflanzte Leiter bis 0,40*):

| | |
|---|---|
| **Leiter** | +0,04 · +0,08 · +0,12 · +0,20, je 5 Wiederholungen, Teil 1 und Teil 2 (`--leiter`) |
| **Auflösung** | die kleinste Stufe mit ≥ 4 von 5 |
| **Ursache mitmessen** | Teil 1: wie viel der Pflanzung in der frühen Auswahl **ankommt** und wie viel des Pflanzbereichs die Auswahl **deckt**; Teil 2: Deckung der oi-Auswahl — *Erklärung messen statt vermuten* |
| **Urteil L2/L5** | nur, wenn der gemessene Abstand zum Nullmittel **größer als die Auflösung** ist **und** über dem Band liegt; sonst **„nicht auflösbar“** — ausdrücklich **nicht** „trägt nicht“ |
| **keine Stufe bis +0,20** | die Anlage kann die Frage nicht beantworten → die Kurve bleibt **Auskunft**, und die Form der Messung muss neu vorgelegt werden |

⚠️ Die Kriterien L2–L7 selbst bleiben **unverändert**. Die Leiter läuft nach der Kette auf `bestand`.


---

## 11. ERGEBNIS (29.09.2026) — Befund 2.685

> **Urteil in einer Zeile:** Kein Sweet Spot beim Anfahren nachweisbar — die rsi-Auswahl trägt in **jeder** Phase,
> absolut am meisten in der **Fahrt**; ein Anfahr-Vorteil von +0,08 oder mehr ist **ausgeschlossen**, kleinere kann die
> Anlage nicht auflösen.

| # | Ergebnis (bestand / unverzerrt:1 / :2 / :3) |
|---|---|
| **L0** | ✔ E2g bitgleich; rsi allein bitgleich zu 2.680 in allen vier Mengen |
| **L1** | ⛔ an +0,04 (2 von 5, 3 von 5) · **Leiter: Auflösung +0,08 in beiden Teilen**; Ursache gemessen: bei +0,04 deckt die geschätzte Auswahl den Pflanzbereich nur zu 0,26–0,98 |
| **L2** | früh − spät fest −0,064 / −0,043 / −0,051 / −0,049 = **das Nullmittel** (Abstand −0,007..+0,005) → **nicht auflösbar**; rollierend 2 von 4 knapp über dem Band |
| **L3** | ✔ früh > 0 in jedem Jahr, auch 2022 (4 von 4) |
| **L4** | ✔ früh bei 77–86 % der Assets positiv |
| **L5** | funding 4 von 4 fest und rollierend über dem Band — aber +0,014..+0,026 über dem Nullmittel, **unter** der Auflösung → nicht auflösbar · oi 0 von 4 · konten nur rollierend |
| **L6** | ⛔ funding Eigen 1 von 4, Markt 2 von 4 → Rolle **Kontext** |
| **L7** | die Kurve **steigt** mit der Nadel (fest 0..0,5 +0,076..+0,080 · 1..2 +0,104..+0,123) — aber alle Anker der Klasse steigen mit: die Nadel ist **selbst Fortsetzung**; 72 h holt das Anfahren nichts auf; rsi auf stehenden Ankern +0,053..+0,061 |

**Was folgt:**
1. Die Tachonadel ist **kein Gewicht** auf A (Doppelzählung mit rsi) — sie geht **nicht** in die Auslösung. Ob in die Mail: **offen** (Nutzer: *abstrakte Zahl, bereits jetzt zu viel Information — das müssen wir besprechen*).
2. rsi (A während) trägt auch beim Anfahren und auf stehenden Ankern — **keine Phasensperre** für K5.
3. A **vorher** bleibt ohne Beleg: funding klein und vor allem Markt.
4. Die Messform mit geschätztem Modell löst auf Teilmengen erst +0,08 auf — für kleine Effekte braucht es eine Auswahl
   mit fester Richtung aus dem Training.

⚠️ **Nachträglich gesehen, nur Hypothese:** Der Zuwachs von rsi innerhalb der Klasse ist bei 0..0,5 ATR am größten
(+0,065..+0,072) und nach einem Rückgang (−1..0) fast null — das ist das Nutzerbild *0 auf 20*, aber unter der
Auflösung und nicht vorab benannt.

---

## 12. ZWISCHENFAZIT ZUM ZIEL — Vorschlag, noch NICHT abgestimmt (29.09.2026)

**Ziel:** je Asset und Handlung eine begründete Aussage über das **Potential**; ein Signal, wenn ein bestimmtes
Potential erreicht ist.

| Baustein | Stand nach 2.685 |
|---|---|
| **A · OB** (Signal) | ✔ **ein** belegtes Signal: rsi (Fortsetzung) — P(+5 % vor −5 %) im obersten Zehntel rund **5–8 Punkte über dem Normal** des Assets, in jeder Phase, fast kalibriert. *Vorher* (früher Einstieg): **nichts** Belegtes |
| **B · WIE WEIT** | gemessen, aber **keine Zahl** je Signal (nicht kalibriert) |
| **C · WIE VIEL HEBEL** | ✔ die ATR sagt die Liquidationsgefahr; 5x kalibriert |
| **K5 · ab wann** | offen — Schwelle und Stufen |
| **Nachweis ungesehen** | offen — Simulation, Monate ab 2026-09 |

**Was 2.685 zum Ziel beiträgt:** Der Einstieg wird **einfacher** (keine Phasenregel), und ein **früherer** Einstieg
bringt nach unseren Daten nichts. Das Potential zeigt sich **während** der Bewegung, nicht davor.

**Was fehlt zum Potential:** Heute kann das System sagen *„hier ist die Chance erhöht“*, aber noch nicht *„wie viel“*.
Der nächste Schritt in diese Richtung ist **K6 S** (stärkeres Signal → mehr Einsatz?), danach **K5** (ab welcher
Stärke) und **B** (wie weit).
