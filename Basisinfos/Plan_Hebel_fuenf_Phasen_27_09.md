# Der Hebel in fünf Phasen — Planung und Stand

**27.09.2026** · Nutzervorgabe wörtlich, danach der Abgleich

> Dieses Blatt löst `Bauplan_Hebel_27_09.md` als oberste Liste ab. Der
> Bauplan bleibt gültig für die **technischen** Schritte (Dateien,
> Reihenfolge, Fallen), ist aber der Phase 1 untergeordnet.

### ⭐⭐⭐ Das REGELWERK zur Bewertung

`Basisinfos/Regelwerk_Hebel_Bewertung_27_09.md` — wie aus einer Messung
eine Regel wird. **Einstieg misst gegen die CHANCE, Hebel gegen das RISIKO.**

⛔ Entstanden aus der Nutzerkritik vom 27.09.: *„Was ist mit turnover und
funding, diese waren bereits gesetzt oder?“* — an einem Tag zehn
Kursmerkmale gemessen und die **drei registrierten Träger** nie geladen.

---

### ⭐⭐ STAND 28.09.2026 — wo Phase 1 steht

| | |
|---|---|
| ✔ **Anwendungsebene abgestimmt** | K1–K7 (27.09.), Regelwerk *Stand 28.09.* · Voranalyse `Voranalyse_Kombination_Anwendungsebene_27_09.md` |
| ✔ **Messbasis vervollständigt** | 137 eingestellte Paare plus Terminmarkt nachgeladen (2.668/2.669), `--menge unverzerrt` |
| ✔ **K3 gemessen** | Kontextfläche ohne Feld, Dominanz-Sperren fallen (2.670/2.672) |
| ✔ **K1 Schritt 1 gemessen** | Wirkungskurven je Beitrag (2.671, 2.673, 2.674) und das vorab festgelegte **Randkriterium** mit **Regeltest** (2.675) |
| ✔ **Altersachse gemessen** | gültig, keine Umkehr; der **24 h alte** Wert trägt in Suche, Prüfzeit und 2022; die Tagesperiode ist kein Uhrzeit-Artefakt (2.676, löst 2.675 ab — dessen Altersachsen-Satz war ein Lesefehler). **Kein Blocker**: Alter und A4 werden Gewichte |
| ⛔ **K1 Schritt 2 gemessen** (2.677) | die Kombination als **Kurvenmodell** trägt nicht (T1–T3 in keiner Menge) — die Regel ist sauber (Zufall schweigt), aber die **Auflösung** reicht nicht (+0,16 statt der gesuchten +0,03…+0,06); der Marktmedian steht für die Zeit. Die Wirkung ist da: wo *oben gestreckt*, liegt q ungesehen +0,07…+0,10 über der Schätzung |
| ⛔⭐ **K1 Schritt 2b gemessen** (2.678) | trägt nach dem Vorabkriterium nicht — die Kombination ist schlechter als rsi allein. **Ursache**: wer nach Normal + Beitrag auswählt, wählt das **Phase-Normal**, und das kehrt zur Mitte zurück. Nach dem **Beitrag** allein ausgewählt: q +0,05 über dem Normal in allen vier Mengen, auch rollierend — etwa so viel wie der rsi-Rand allein |
| ✔ **K5 entschieden** (28.09., vorläufig) | Schwelle auf dem **Beitrag** (Vorsprung gegen das eigene Normal) — *trägt auch das nicht, wird neu abgestimmt* |
| ✔ **K7 gemessen** (2.679, 28.09.) | am **echten Bitpanda-Buch** (37 Abschnitte, 7 Liquidationen aus der Gebührensignatur): der **Markpreis** wird Hauptmaß; m = 0,09 liquidiert zu früh, nie zu spät; alle Fehlalarme in Büchern **über 5x**. ⚠️ Der Importer teilt die Positionen falsch ein (Teilschließungen) — eigene Voranalyse, spätestens Phase 2 |
| ⛔◐ **K1 Schritt 2c gemessen** (2.680, 29.09.) | die Auswahl nach dem **Beitrag** ist robust (T6: in jedem Drittel des Normals positiv; jedes Jahr, 80–86 % der Assets) — aber **nicht mehr als rsi allein** (T2) und **nicht kalibriert** (T3, Steigung 0,42–0,55). Nach der Vorabfestlegung: **K5 wird neu vorgelegt** |
| ◐ **K6 gemessen** (2.681, 29.09.) | Spot-Tief **und** Markpreis, je vier Mengen: die **ATR allein** sagt die Liquidationsgefahr voraus, die Risikokurven bringen **nichts** dazu; **5x** vorwärts kalibriert, **3x** nur geordnet, **2x** zu selten. Tabelle liegt vor (Grenze 1 %/72 h: 3x 20–25 %, 2x 75–78 % der Anker, eingetreten unter der Grenze). ⚠️ **H0** (auf der Einstiegsauswahl) und **J10** (10./11.10.) offen |
| ⛔ **K5 neu gemessen** (2.682, 29.09.) | **Tor nicht bestanden — kein Urteil.** In der Kombination bestimmt rsi die Auswahl, eine Wirkung der Lage wird verdeckt (gepflanzte +0,04 kommen als +0,004 an). Die Lage muss **zuerst für sich** gemessen werden |
| ◐ **K5-Folge gemessen** (2.683, 29.09.) | **rsi allein zeitstabil** (jedes Jahr, auch 2022) und **roh fast kalibriert**; das Phase-Normal ist größtenteils Rauschen, die **Schrumpfung** behebt die Rückkehr zur Mitte; die Lage hat einzeln klare Kurven, in der Kombination kommt nichts an (Tor ⛔) |
| ◐ **Gegenprüfung** (2.684, 29.09.) | rsi hält gegen das **geschrumpfte** Normal (Verzerrungsanteil ~0), 2024 schwach; rsi misst die **laufende** Bewegung (RSI der letzten 14 h) — Fortsetzung, kein OPTIMUM |
| ✔ **Rollen geprüft und im Standblatt** (29.09.) | das Schema vom 25.09. hält: **A** Richtung entscheidet **OB** (vorher = OPTIMUM, nur Kandidaten; während = Fortsetzung mit rsi, eigener Einstiegstyp) · **B** Bewegungserwartung **WIE WEIT** (robust, 2.655/2.662) · **C** Risikosperre mit der ATR **WIE VIEL HEBEL** — keine Summe, kein Blocker (`Einordnung_Beitraege_29_09.md`) |
| ◐ **Losfahren aus dem Stand gemessen** (2.685, 29.09.) | **kein Sweet Spot beim Anfahren** nachweisbar: die rsi-Auswahl trägt in **jeder** Phase (jedes Jahr, 77–86 % der Assets), absolut am meisten in der Fahrt; ein Anfahr-Vorteil ≥ +0,08 ausgeschlossen, kleinere nicht auflösbar (Leiter: Auflösung +0,08). Die Tachonadel ist selbst Fortsetzung → **kein Gewicht**; ob in die Mail: **offen** (Nutzer: *abstrakte Zahl, schon zu viel Information*). funding auf stehenden Ankern über dem Band, aber unter der Auflösung und vor allem Markt → Kontext |
| ◐ **K6 S Stufe 1** (29.09.) | die Signalstärke erreicht die Weiter-Schwelle nur auf der Kante (+0,0408), nur 2025, nicht monoton — keine Vollmessung; R2 (Lage-Extreme) zurückgestellt |
| ⛔◐ **Wetter gemessen** (2.686, 29.09.) | Begriffe **Beitrag · Kontext · Gewicht · Sperre** abgestimmt (Regelwerk). Das Wetter (BTC 30 Tage) als Gewicht auf rsi ist ab 2024 **nicht nachweisbar** (+0,029 in der Betriebsform, Nullwelt P90 +0,112, wenige Wetterlagen) — nach der Abbruchregel die letzte Wettermessung. ✔ rsi trägt in **jedem** Wetter und Jahr |
| ◐⭐ **K5 Wahl 2024** (2.687, 29.09.) | der **Zustand** (rsi oben) ist als Zahl **nicht kalibriert** und ordnet 2024 nicht — keine Schwelle darauf. Der **Ersteintritt** (erstes Überschreiten, Einstieg 1 h später) trägt **+0,076..+0,093**, weit jenseits der Nullwelt (Nutzereinwand *nicht aufs fahrende Auto aufspringen*) — **Kandidat**, nur 2024 |
| ⛔ **Korrektur (29.09., Nutzer)** | die **Schwelle** gehört ans **Ende von Bewertung 1** — auf die **Summe** der Chance-Beiträge (Regelwerk § 1/§ 4, E-4), nicht auf rsi allein. K5 ist **zurückgestellt**, bis die Summe steht. Aus 2.687 bleibt ein **Messform**-Befund für den rsi-Beitrag (Zustand nicht kalibriert, Ersteintritt trägt). Prüftakt und Cooldown sind **Phase 2** |
| ✔⚠ **KERN Schritt 1 bestanden** (2.688, 29.09.) | der Ersteintritt (s = +0,035, per Regel auf 2024 gewählt) trägt **einmal bestätigt 2025–26 in 4 von 4 Mengen** (+0,059..+0,076, B1–B6). ⚠️ Nicht besser als der Zustand; stark **regimeabhängig** (2025 klein, Juli–Dezember 2025 negativ) |
| ✔⚠ **KERN Schritt 2 H0** (2.689, 29.09.) | die ATR-Tabelle unterschätzt das Risiko der Einstiege **nirgends** (5x: 12 h 0,40–0,45, 24 h 0,48–0,59, 72 h 0,76–0,81 beobachtet/geschätzt) — **vorsichtig, kein Aufschlag**; 2x nur Black Swan. ⚠️ Der Kern ist ein **Tageshandel**: +5 % im Median nach 19–20 h |
| ⛔✔ **KERN Schritt 3 Simulation** (2.690, 29.09.) | Wahl 2024: 24 h, ohne Ziel, Grenze 2 % (Konto ×1,24). **Bestätigung 2025–26: das Hebelkonto verliert in 4 von 4 Mengen** (×0,26–×0,62), Spot um null — das **Signal schlägt den Zufall** klar, aber der **Rohvorteil je Handel (+0,12..+0,33 %) liegt unter den Bitpanda-Kosten eines Tageshandels (0,48 %)**; Kostenbasis am echten Buch geprüft |
| ⭐ **LÖSUNGSWEG zum Ziel** (30.09., Vorschlag zur Abstimmung) | W1 **L2** den Kern anheben (jetzt) · W2 **Potential** als zweite Zielgröße · W3 **Short-Kern** gegen das Regime · W4 **Positionsführung** mit nachgezogenem Stop (Phase 5) · W5 **Datenquellen** für *A vorher* · W6 L3/L1 später — Einzelheiten `Voranalyse_L2_Kern_anheben_30_09.md` Abschnitt 10 |
| ⭐ **OPTIMIERUNGSLOOP** (Nutzer 30.09.) | *das Optimierungsthema werden wir über mehrere Ebenen ausreizen* — je Ebene (Regelparameter · Beiträge auf dem Kern · Summe · Positionsführung) dasselbe Verfahren: **Wahl auf 2024**, **einmalige** Bestätigung 2025–26, später die neuen Monate ab 2026-09. Erste Ebene: **N2 Ruhe davor** (L2 Abschnitt 13). ✔ L2 bestätigt (2.691): Stärke ordnet nicht (Schalter); **48 h Ruhe** davor 3/4; **ema_abstand_atr** und **volumenschub** oben heben das **Potential** ATR-frei (4/4, 3/4); vola_kausal ist die ATR (G-ATR). ➤ N3 Überschneidung, dann Summe L4, N4 Simulation |
| ➤ **nächster Schritt (30.09. vormittags)** | ✔ L2 bestätigt (2.691, Voranalyse L2 Abschnitt 15) — ✔ **N3 abgestimmt** (P1–P5, `Voranalyse_L2_N3_Ueberschneidung_30_09.md` Abschnitt 8), ✔ **N3 bestätigt (2.692)**: die Form per Regel **ema_abstand_atr + Ruhe 48 h** trägt (3/4, 4/4); volumenschub 2025–26 in 4/4 eigen → **Vergleichsarm**; *beide oben* Potential +0,22 ATR (Kern +0,06), **nicht** die Chance. ✔ **L4 abgestimmt** (Q1–Q5, E-28; dazu L4-5 **Spiegel** als Urteil vor der Rechnung), ⛔ **L4 bestätigt NICHT (2.693)**: der **Spiegel fällt** 4/4 — die Wucht wählt größere Bewegungen in beide Richtungen (2025 nach unten, 2026 nach oben), keine bessere Richtung; Rolle B gehört in Positionsführung/Hebelstufe; E-28 greift nicht. Es trägt **Kern + Ruhe 48 h**. ➤ zur Abstimmung: N4 mit Kern + Ruhe 48 h, danach die **Richtung** (H-Schalter, Short-Kern W3) — Überschneidung ema_abstand/volumenschub/Ruhe 48 h, dann **Summe (L4)**, **N4** Simulation als Erfolgsmessung |
| ⭐ **ZWISCHENFAZIT 30.09. mittags** (Nutzer: *wo stehen wir, ist der Weg der richtige?*) | **Stand:** Der Kern trägt ungesehen, ist aber klein und verliert an den Kosten (2.688/2.690). L2/N3 haben das **Potential je Einstieg** gehoben: Ruhe 48 h, ema und volumenschub; *beide oben* etwa das Vierfache (2.691/2.692). Das Risiko bleibt bei der ATR, ein Artefakt wurde erkannt und aussortiert (vola_kausal). **Nicht erreicht:** die **Chance** steigt nicht, die **Wirtschaftlichkeit** ist ungeprüft (N4), *A vorher* (früher Einstieg) fehlt. **Urteil des Experten:** Der Weg ist richtig, mit drei Korrekturen: (1) das **Potential** als Zielgröße der Summe ausdrücklich machen (L4 Q1), (2) ein **Vorwärtstest** auf den Monaten ab 2026-09 als fester Teil des Optimierungsloops, weil 2025–26 mit jeder Ebene weiter *verbraucht* wird, (3) W4 (Gewinner laufen lassen) und W5 (Quellen für *vorher*) nicht aus dem Blick verlieren, denn größere Bewegungen belohnen eine gute Positionsführung |
| ⭐ **H-SCHALTER** (Nutzer 30.09., **nach Kern heben / nach L4**) | ✔ Nutzer 30.09.: *„dein Hinweis zur Stärke ist wichtig — als **optionale Prüfung**, wie weit die **Richtung** noch optimiert werden kann“*, also Rolle A (rsi) weiter ausreizen. *der Kern ist ein Schalter* (2.691 A1) war **nicht Absicht** — noch einmal als **Hypothesenfrage** gegenprüfen und Vor-/Nachteile bewerten. Gemessen ist nur die Stärke **in der Übertrittsstunde** (80 % der Einstiege zwischen +0,035 und +0,044, kaum Streuung → zum Teil Folge der Einstiegsform). Hypothese: die **Summe** liefert die Abstufung; Gegenhypothese: eine andere rsi-Stärkeform ordnet (Anstieg des Vorsprungs, Abstand nach 1–3 h, Zustandsdauer). Einzelheiten `Voranalyse_L2_N3_Ueberschneidung_30_09.md` Abschnitt 7 |
| (vorher 30.09. früh) | **L2 zuerst** (Nutzer): stärkere Signale **neutral** messen — höheres Potential je Handel, **ohne** Kosten in der Auswahl; die Wirtschaftlichkeit zeigt danach die Simulation (Erfolgsmessung). Dann L4 (Summe), L3 (Haltedauer ohne Hebel); **L1 (Börse) erst Phase 4/5** — die Bewertung bleibt neutral |
| ⏸ *nach dem Kern* | Bewertung 1 als **Summe aller Beiträge** fertig machen: die Lage-Beiträge (funding, konten_verh, oi_aenderung, ema_abstand selbstbezogen) **mit einer Messform, die sie auflöst**, neben rsi in die Summe — dann erst die Schwelle auf der Summe · Bewertung 2 als Summe der Risiko-Beiträge (ATR + Lage-Extreme) |
| ⏸ *überholt* | **K5 neu abstimmen** (Nutzer) — mit der einfacheren Regel *rsi allein* zur Bestätigung und der OPTIMUM-Frage (rsi misst die Bewegung) · **K6** mit dem Markpreis auswerten (danach H0: auf der Einstiegsauswahl) · dann **Simulation Ebene 3** |

Die Reihenfolge im Einzelnen steht unter *Was Phase 1 noch verlangt*, Zeile 2.

---

### ⚠️⚠️ Der Faktenteil kommt aus Code — hier steht die Planung

```bash
python hebel_neubau.py
```

**Nutzerkritik 27.09.:** *„wir haben einen Hauptplan — wenn du wieder
etwas Neues parallel machst, bringt das nichts."*

| | |
|---|---|
| **Dieses Blatt** | die **Phasen**, die Reihenfolge, die Entscheidungen — die oberste Liste |
| `hebel_neubau.stand()` | der **Faktenteil**: welche Rolle steht wo, auf welcher Geometrie, mit welchem Befund |

⚠️ Und damit sie nicht auseinanderlaufen, **liest** `stand()` die Phasen
aus *diesem* Blatt, statt sie zu kopieren. Ändert sich hier das Format,
bricht es ab — es gibt keinen stillen Rückfall auf eine zweite Liste.

⛔ **Wozu das gebaut wurde:** Auf die Frage *„zeige mir den aktuellen
Hebel-Einstieg"* habe ich `agent/betraege.py` vorgelegt — Kelly,
Basisrate, `funding_fuenftel`. Also den **alten Spot-Ablauf** als
Ist-Stand des Hebels. Der Riegel dagegen (`pruefe_quellen`) stand seit
dem Vortag da und griff nicht: er bewacht **Messskripte**, ein Bericht ist
keines. Jetzt kommt der Bericht aus Code, der den Spot-Arm nicht kennt —
nachgewiesen am **Seiteneffekt** (`python hebel_neubau.py --nachweis`).

---

# Die fünf Phasen

| # | Phase | Nutzervorgabe |
|---|---|---|
| **1** | **Grundlage** | *„Messen und die Bewertungen und die fachliche und technische Grundlage zu schaffen — muss sauber über **alle Beiträge** funktionieren (hier sind wir noch immer, Binance, CoinGecko, oder andere Quelle?). Kalibrieren der Hebel, etc."* |
| **2** | **Prüfung an Echtdaten** | *„Prüfung der Messungen anhand von Echtdaten (alle) und **aktuellen Hebelpositionen (Portfolio)** und funktioniert das System am Papier mit historischen Daten (nur Desktop) auf Herz und Nieren — oder müssen wir nachjustieren, da zu wenig oder zu viele Signale entstehen (jetzt kommt **Prüftakt und Cooldown** ins Spiel)"* |
| **3** | **Ablaufkette** | *„Wenn die Basis und das System funktioniert: Hebel über die **gesamte Ablaufkette** prüfen und die **LLM-Bewertung** anpassen, wo erforderlich"* |
| **4** | **Produktion** | *„finaler Umbau und in Produktion für **Einstieg und Hebelbewertung**"* |
| **5** | **Ausbau** | *„nachgelagerte Punkte — Krypto und Hebel final ausbauen mit **Hebelpositionsführung** (Trailing?) und **Ausstieg**"* |

**Wir sind in Phase 1.**

---

# ⛔ Die Trennung, an der ich gescheitert bin

> **Nutzervorgabe 27.09.:** *„DIE BEWERTUNG MUSS NEUTRAL OHNE ERTRAG
> erfolgen — der Ertrag oder Positionsgröße ist NACH der Bewertung
> relevant. Zum Zeitpunkt der Beitragsprüfung ist DAS RISIKO und somit der
> HEBEL zu bewerten. Halte deine Messungen zur Erfolgsmessung mit den
> Betriebsbedingungen auseinander."*

| Ebene | Frage | darf verwenden | darf **nicht** |
|---|---|---|---|
| **A · Bewertung** | Ist diese Lage gut? Welcher Hebel ist bei diesem **Risiko** vertretbar? | Kurs, EMA, ATR, Stopabstand, Zielabstand, RM-11 — alles zum **Entscheidungszeitpunkt** bekannt | ⛔ Ertrag, `q`, CRV aus Ergebnissen, Kelly, Positionsgröße, Kapazität |
| **B · Erfolgsmessung** | Trägt diese Regel? | Erträge, Nullwelt, Weglassprobe, Zeitstabilität | ⛔ zurückfließen in A |
| **C · Betriebsbedingungen** | Was kommt von den Signalen an? | Kapazität, Symbolsperre, Prüftakt, Cooldown, Kontingent, Datenlage | ⛔ als Qualitätsurteil gelesen werden |

⚠️ **Mein Fehler:** Ich habe die **Schwelle** — eine A-Größe — als
**Kelly-Nullstelle** bestimmt. Kelly kommt aus `q` und CRV, also aus
**Erträgen**. Und dann habe ich C (Kapazität, Positionsgröße) in dieselbe
Tabelle gelegt und daraus über A geurteilt.

---

# Der Stand — Befund für Befund, nach Ebenen sortiert

## ✔ Gültig — Ebene B (Erfolgsmessung)

| Befund | |
|---|---|
| **2.606** | EMA-Länge **48 Stunden** ist gemessen; der klassische 50-Tage-EMA ist wertlos (MFE/MAE 1,00) |
| **2.625/2.626** | Die Achse ist **invers** und trägt — 12 von 12 out-of-sample, 115 von 115 Symbolen |
| **2.628** | Geometrie **H24 / Stop 1,00 ATR / Trailing 1,5 / 0,5** |
| **2.629** | Die Kalibriergrenze ergibt sich aus den Kosten; Stop 1,00 ist auch netto optimal |
| **2.633** | Die **Auswahl** trägt 5 von 5 Jahren und in jeder Weglassprobe. ⛔ Die **Stufung** 5/4/3/2 trägt nicht — sie hing an 2025 |
| **2.635** | Auf **Tagesbasis** trägt die Achse **nicht** — keine der sechs EMA-Längen, keine Teillösung |
| **2.636** | Stundendaten machbar: **7-Tage-Fenster** reicht (100 % gleiche Auswahl), Binance am NB erreichbar, Verzögerung bis **6 Stunden** trägt noch |
| **2.637** | **Skalenfaktor 2,0832** für Quellen ohne High/Low — je Symbol (2,6 % Streuung) und über 5 Jahre stabil |

## ✔ Gültig — Ebene C (Betriebsbedingungen)

| Befund | |
|---|---|
| **2.634** | ⛔ **Der Hebel kann heute gar nicht entstehen**: kein Beitrag gilt für `instrument="hebel"`, Kelly im Code ist exakt **0,0**. Das ist der Ist-Zustand, kein Urteil |
| **2.638** | Der Betrieb kauft nur **Streckenanfänge** (29,1 % der Anker). Die **Trennschärfe bleibt** (+2,78 gegen +2,83), der absolute Ertrag fällt |
| **2.623** | **Z-2** (`crv_minimum` 2,0) ist tautologisch und gehört entfernt |
| **2.621** | Längste **Verlustserie 198–199** über alle Stopweiten — nicht wegkalibrierbar |
| *aus 2.640* | ⚠️ Ohne High/Low zerfällt die Reihe in **mehr, kürzere Strecken** (2,32 gegen 2,92 Anker) und feuert **2,29×** so oft. Mengenfrage, keine Ordnungsfrage |

## ⛔ Zurückzuziehen — Ebene A aus Ertrag abgeleitet

| Befund | warum |
|---|---|
| **2.630** | Hebelkurve und Hebelhöhe aus **Kelly** — war schon durch 2.632/2.633 korrigiert, ich habe den Fehler dann wiederholt |
| **2.632** | Schwelle **−1,2881** als Kelly-Nullstelle |
| **2.640** | Schwellen **−1,65 / −2,20** ebenso. ⚠️ Der **Quellenvergleich** darin bleibt gültig (Ebene C) |
| **2.639** | ⛔ **Doppelt falsch**: Positionsgröße 20–50 % statt der echten 1,2–7,8 % (`r_min` 0,5 %, `r_max` 1,25 %), **und** die Frage gehört gar nicht in die Bewertung |

---

# ⛔⛔⛔ Die Korrektur vom 27.09. abends — ich war im falschen Arm

> **Nutzervorgabe:** *„WIR sind bei einem NEUBAU des Hebels, die alten
> Beiträge sind nicht relevant. NUR HEBEL UMBAU … trenne ALT von NEU,
> sonst killt uns der Umbau."*

## Die drei Rollen — aus dem Neubauplan vom 25.09.

| Rolle | Frage | Testform | Kandidaten | Stand |
|---|---|---|---|---|
| **A Richtung** | geht es aufwärts? Trendumkehr? | monotone Ordnung **plus Spiegelprobe** | `trendstruktur` (mehrere Zeitebenen), `ema_lage`, `ema_steigung`, **`rsi_aenderung`** (tief *und steigend*) | ⛔ **nicht gebaut** |
| **B Bewegungserwartung** | kommt überhaupt etwas? | gegen die **Auflösungsrate**, nicht gegen `q` — B ist richtungslos | `bandenge` (Squeeze) | ⛔ **nicht gebaut** |
| **C Risikosperre** | überdehnt, überhitzt? | **Ausschlusstest** — verbessert das Weglassen des Extrems den Rest? | **`ema_abstand_atr`** | ✔ gemessen (2.642) |

**Anordnung: `A ∧ B ∧ ¬C`** — keine Summe, kein gemeinsames Fünftel.

⚠️⚠️ **Überholt als Anordnung (Stand 28.09.):** E-4 (*„der Hebel ist ein
Beitragssystem und KEIN Blocksystem“*) und K1 (Wirkungskurven, Summe der
Kurven) ersetzen `A ∧ B ∧ ¬C`. Gültig bleibt die **Rollenfrage** je
Merkmal (Richtung, Bewegung, Sperre) — sie steht jetzt in der Rolle
jedes Rands (Einstieg / Sperre, 2.675). ⚠️ Die Tabellen `ROLLEN` und
`KANDIDATEN` in `hebel_neubau.py` führen noch die alte Anordnung und
sind von einer Wache festgehalten — nachzuziehen ist das in einem eigenen
Schritt mit Vorlage, nicht nebenbei.

⭐⭐ **`ema_abstand_atr` ist Rolle C.** Ich habe sie zwei Tage lang als
Einstiegssignal vermessen. 2.642 („Risiko-Filter, kein Ertragsfilter")
ist damit **kein Rückschlag, sondern die Bestätigung ihrer Rolle**.

## ⛔ Dreimal in den Spot-Arm zurückgerutscht

| | |
|---|---|
| **1** | `funding_fuenftel` / `turnover_fuenftel` als „unsere Beiträge" behandelt — beide `instrumente=("spot",)`, auf H20 und `bewegung_r` gemessen |
| **2** | die **Kelly-Nullstelle** als Bewertungsschwelle benutzt — dieselbe Formel, mit der der Spot-Arm seine Quote rechnet |
| **3** | die **Risikosperre** als Einstiegssignal vermessen |

✔ **Der Riegel steht jetzt im Code** (`hebel_neubau.pruefe_quellen`) und
wird vom Suite-Paket **`Hebelneubau`** bewacht (10 Prüfungen).
⛔ **Der produktive Spot-Arm wurde NICHT stillgelegt** — er führt offene
Positionen; das braucht einen eigenen Auftrag.

## Die Abdeckung für den Hebel — gemessen 27.09.

| | Symbole | Anteil |
|---|---|---|
| `asset_hebel_settings` freigegeben | 43 | 100 % |
| mit Stundenkursen (≥ 300 h) | 28 | **65,1 %** |
| ⚠️ **davon liquide** (≥ 100.000 USD/h) | **15** | **34,9 %** |

APT · AVAX · BNB · BTC · ETH · INJ · **KAITO** · LINK · NEAR · ONDO ·
SOL · SUI · TAO · VIRTUAL · XLM — ⚠️ gegenüber 2.611 **KAITO statt
RENDER**, die Grenze ist beweglich. Mit dem Laderfix → 86 %.

⛔ **Korrigiert 27.09. abends (E-8):** hier stand *„`funding` und
`turnover` … Spot-Quellen, hier irrelevant"*. Das war falsch und genau
der Fehler, den 2.651 benennt. Die Spot-**Quellen** sind nicht
irrelevant — sie wurden für H20 optimiert und vermessen; nur ihre
**Anwendung** wird auf den Hebel dimensioniert (kurzer, intensiver
Handel). Tot für den Hebel ist Spot in seiner **heutigen Form** (Code und
Produktion). Beim Betrieb zählt, ob die **Quelle live beschaffbar** ist,
nicht was der heutige Sammler holt — Nutzer: *„der aktuelle Betriebscode
ist veraltet."*

# Was Phase 1 noch verlangt

| # | offen | |
|---|---|---|
| **0** | ✔✔ **1a ERLEDIGT (2.642)** — der Horizont ist kein Eingang, sondern ein **Messfenster**. Gemessen regelfrei in ATR: die Achse ist ein **Risiko-Filter** (d 0,521 auf MAE) und kein Ertragsfilter (d 0,267 auf MFE), stabil in 5 von 5 Jahren. ⛔ *Kurz* trifft nicht zu — die Auswahl braucht 10,5 % **laenger** bis zum Hoechstpunkt. ⭐ Die Bruecke zum Hebel steht damit **ohne Ertrag**: 0,75 statt 1,08 ATR Rueckgang heisst niedrigere Stopwahrscheinlichkeit, also mehr Hebel | *erledigt* |
| **1** | ⭐ **Die Bewertungsebene neu aufsetzen — sie ist NEUTRAL.** Nutzer 27.09.: *„die BEWERTUNG soll, wenn möglich, OHNE auskommen — eine Zeitpunktbewertung, die Lage und das Risiko (Beiträge bestimmen) — ohne Geometrie, ohne Ertrag, das kommt danach. Zum MESSEN und PRÜFEN als Vergleich und Erfolgsrechnung — ja, da sollen Kurs und ggf. Stop, erreichtes Ziel etc. Verwendung finden, nicht in der Bewertung, die ist NEUTRAL."* ⛔ Hier stand bis 27.09. abends *„Chance-Risiko-Verhältnis aus Stop- und Zielabstand"* — das ist Geometrie in der Bewertung und widersprach dem Regelwerk. ➤ Bewertung 1 (Lage) und Bewertung 2 (Risiko) kommen aus den **Beiträgen**; Stop, Ziel und Kurs gehören in Ebene B/C (2.641) | *nächster Schritt* |
| **2** | ⚠️ **„muss sauber über ALLE Beiträge funktionieren"** — ◐ **Teil erledigt:** die registrierten Träger und die Terminmarkt-Merkmale sind auf **Bewertung 1** gemessen — `funding` (mit dem **Vortageswert**, 2.663: die Hälfte des alten Lifts war Vorgriff), `oi_aenderung`, `konten_verh` tragen bei k = 0, **keiner mit Vorlauf**; `turnover` und die übrigen fallen. Die **Höhe** hält den Pflichtablauf (2.662); die Datenfehler aus 2.658 verschieben kein Urteil (2.664). Stand je Merkmal: `python hebel_neubau.py`. ✔ **E2 mit den Richtungsdaten ist gelaufen (2.665):** 4 von 88 halten den Pflichtablauf, 0 von 80 Zufallsauswahlen; nur **funding** ist Lage vorher — und klein; der Käuferanteil begleitet die Bewegung. **Offen, in dieser Reihenfolge (Nutzer 27.09.: *sauber und langsam, bis wir die Grundlagen haben*):** ✔ **Such-/Prüf-Trennung für funding gelaufen (2.666):** funding **hält auf 2022** in derselben Größe (die erste Fassung *dreht* war ein Mitternachtseffekt) und markiert zusätzlich die **Phase** des Assets. ✔ **Höhe in ATR (2.667):** die Prozent-Höhe ist größtenteils die ATR selbst; für die Liquidation ist die ATR zum Einstieg das Risikomaß. ⛔ Den Käuferanteil 2021/22 nachzuladen lohnt nicht: er **begleitet** die Bewegung (2.665), mehr Daten ändern daran nichts. (a) ⭐ **Die ANWENDUNGSEBENE** — bisher ist jeder Beitrag **einzeln** gemessen; die **Kombination** je Asset und Zeitpunkt (Nutzer: *ein Beitrag ist selbst schwach, in Kombination stärker*) ist ungemessen. Voranalyse und Abstimmung vor dem Bau; (b) **Höhe in Prozent und in ATR nebeneinander** — danach die Nutzerentscheidung, welche Einheit Bewertung 2 misst; (c) **Vorlauf** bei H72/H120; (d) **Bewertung 2** für dieselben Träger. ⭐ **STAND 28.09.:** ✔ (a) **abgestimmt** als K1–K7 (27.09.); ✔ (b) entschieden durch **K6**: Bewertung 2 misst die **Liquidationsgefahr in Prozent am Markpreis**, die ATR zum Einstieg ist das Risikomaß (2.667); ✔ die Prüfung von K1–K7 fand die **Überlebensverzerrung** (2.668) → **137 Eingestellte nachgeladen**, Messbasis `--menge unverzerrt` (2.669); ✔ **K3** ohne Feld (2.670), Dominanz-Sperren fallen (2.672); ✔ **K1 Schritt 1**: ema_abstand selbstbezogen trägt als Kurve (2.671), funding/Premium geteilt, Asset-Anteil trägt nicht (2.673), **Randkriterium mit Regeltest** (2.675): rsi/momentum oberer Rand trägt je Asset, funding_markt unten nur in der Suche, *viele Longs je Asset* hält nicht. **Offen, in dieser Reihenfolge:** ✔ (e) die **Altersachse** — gemessen (2.676): gültig, der 24 h alte Wert trägt in jedem Zeitraum, kein Blocker; (f) **K1 Schritt 2** — die Kurven **gemeinsam** schätzen (rsi/momentum/ema_abstand korrelieren, eine Information), Log-Odds, je mit dem aktuellen **und** dem 24 h alten Wert, A4 als abnehmendes Gewicht — ⛔ als Kurvenmodell gemessen und verworfen (2.677: Auflösung zu grob, Markt steht für die Zeit); **neu vorzulegen**: Asset-Beiträge als Ränder, längeres Fenster, Auflösung vorab nachgewiesen; (g) **K6** Hebelstufe aus der Liquidationsgefahr (R, dann R+S); (h) **K7** Markpreis und Abgleich an den echten Positionen (NB-Kopie); (i) **Simulation Ebene 3** — die Regel muss auf ungesehenen Monaten wirken; (j) **Stammsatz** je Asset (S1–S6, vier Symbolwelten ohne Brücke, 2.612) vor jeder Neuaufnahme; (c) Vorlauf bleibt offen. ⭐ **STAND 29.09.:** ✔ (h) **K7** gemessen (2.679, Markpreis Hauptmaß); ⛔◐ (f) der dritte Anlauf **2c** (2.680) löst die Rückkehr zur Mitte, bringt aber nicht mehr als rsi allein und ist nicht kalibriert — **K5 wird neu vorgelegt**; ◐ (g) **K6** mit dem Spot-Tief gelaufen, mit dem Markpreis in Rechnung. ⭐ **STAND 29.09. ABENDS:** ✔ (g) K6 mit dem Markpreis (2.681); Losfahren (2.685), Wetter (2.686) ohne neue Regel; K5 **zurückgestellt** — die Schwelle gehört auf die Summe (E-23); stattdessen der **KERN** Ende zu Ende: ✔ Schritt 1 (2.688, Ersteintritt trägt ungesehen in 4 von 4 Mengen), ✔ Schritt 2 H0 (2.689, ATR-Tabelle vorsichtig, Kern ist ein Tageshandel), ➤ Schritt 3 **Simulation** | teilweise |
| **3** | **Die Quellenfrage**: Binance (28), CoinGecko (16) — oder eine dritte Quelle? | Nutzerentscheidung |
| **4** | **Den Hebel kalibrieren** — aus dem Risiko, nicht aus der Statistik (2.627) | offen |
| **5** | ✔✔ **ERLEDIGT (2.646)** — der Horizont widersprach sich dreifach, weil `HORIZONT_JE_LAGE` **keine Einheit** führte. Jetzt 24 **Stunden** für den Hebel, 20 **Handelstage** für Spot, Einheit in eigener Tabelle, Wächter in der Suite | *erledigt* |
| **6** | **Stundendaten in den Betrieb** — technische Grundlage, ohne sie trägt nichts (2.635) | geplant, nicht gebaut |

## ⛔ Die Grundlage aus 2.647 — ÜBERHOLT durch 2.656

⛔⛔ **Der Ertrag unten (84×) kam aus der Trailing-Regel, nicht aus der
Lage** (2.656: 2.626/2.631 bitgleich reproduziert, ohne Trailing ist das
untere Ende der Achse kein Einstieg). Gültig bleibt die **Methodik** —
gegen das eigene Symbol messen, 99,1 % blieben übrig, also kein
Asset-Rang — und die **Risikorolle** von `ema_abstand_atr` aus 2.642.
Der Rest dieses Abschnitts ist der Stand vom Vormittag.

**Nutzereinwand:** *„wenn du falsch beginnst, sind die Messungen danach
auch wertlos."* Berechtigt — 2.626 hatte nur **tagestreu** gemessen.

| | |
|---|---|
| **absolut** | W ≤ −1,2881 → **+1,2568 %** gegen Markt +0,0150 % (**84×**), monoton über fünf Schwellen |
| ⭐ **je Asset** | gepoolter Lift +1,2418 Pp, **symbolintern +1,2301 Pp** — **99,1 % bleiben übrig**; 84,7 % der Symbole positiv, Konzentration 17,5 % (gleichverteilt wären 9 %) |

⛔ **Damit ist ausgeschlossen, dass die Achse Symbole statt Lagen
sortiert** — der Verstoß gegen Regel 3, den der gepoolte Vergleich nicht
gezeigt hätte.

⚠️ **Die Prüfliste ist deshalb auf SECHS erweitert** (Nutzervorgabe
27.09.: *„nicht den Markt alleine messen, sondern die Bewertung muss auf
das Asset gehen"*). Werkzeug: `messe_grundlage_je_asset.py`, Wächter:
`pruefe_pakete.py --paket Hebelneubau`.

## Was NICHT in Phase 1 gehört

Positionsgröße · Kapazität · Prüftakt und Cooldown *(Phase 2)* ·
LLM-Bewertung *(Phase 3)* · Positionsführung und Ausstieg *(Phase 5)*

⚠️ Genau diese Punkte habe ich in Phase 1 hineingezogen. Sie stehen hier,
damit das nicht noch einmal passiert.
