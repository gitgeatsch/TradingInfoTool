# H-A — die Hebel-Dimension: das Ergebnis

**25.09.2026.** Vorabfestlegung 10 · Plan `Gesamtlage_Hebelumbau_24_09.md`
Schritt H-A. Vorlauf: `HA1_Basislinie_Hebel_24_09.md`.

**Nutzerauftrag:** *„JETZT geht es um den HEBELUMBAU nur HEBEL"* ·
*„prüfen und gegenprüfen"*

---

# § 1 Das Ergebnis in einem Satz

> ⛔ **Kein Kandidat trägt auf der Menge, die der Betrieb sieht — und der
> stärkste liegt unter der Auflösung der Messanlage.**

⚠️ **Das ist eine Rücknahme.** Nach dem ersten Lauf hatte ich K4 und K5 als
tragend gemeldet. Die zwei Nachprüfungen, die danach kamen, kippen das.

---

# § 2 Was gemessen wurde

**116 Symbole, 3,24 Mio Stundenkerzen, Takt 6 h, CRV 2,0, LONG, nur Krypto.**
Zielgröße `ergebnis_r` — Ziel `+CRV`, Stop `−1`, **offen = Zwischenstand**.

| Teil | |
|---|---|
| **A1** | die Basislinie je Haltedauer und Stopvariante |
| **A2** | sechs Kandidaten aus den stündlichen Terminmarktgrößen + Kontrolle |
| **Nachprüfung** | Entflechtung · Monotonie (B5) · beide Hälften (B6) · Trennschärfe · selektierte Menge (F-212) |

---

# § 3 A1 — die Basislinie (unverändert gültig)

| H | offen % | bedingte Quote | Median `ergebnis_r` |
|---|---|---|---|
| **6 h** | 97,1 | **0,1361** | **+0,0000** |
| 24 h | 80,1 | 0,1703 | −0,0334 |
| 72 h | 47,4 | 0,2417 | −0,2502 |
| | | *Nullstelle 0,3333* | |

✔ **R-R11 gehalten** — bei 48 h 30,6 % Stop / 61,1 % offen gegen 29,5 % /
61,3 % aus 2.582 (andere Stichprobe, Tagesbasis).

⭐ **Der Modellfund aus A1 bleibt bestehen** (§ 2 des Vorlaufblatts): die
Kelly-Formel setzt **zwei** Ausgänge voraus, der reale Trade hat **drei**,
und bei 6 h ist der dritte mit 97,1 % die Regel. **Ein `q` aus 2,9 % der
Fälle steuert die Hebelhöhe für 100 %.**

---

# § 4 A2 — die Kandidaten, und wie sie gefallen sind

**Erster Lauf:** `KON zufall` trug nirgends ✔, K4 und K5 trugen auf **allen
fünf** Haltedauern, 12 Treffer bei 3,5 erwarteten.

## 4.1 ✔ Was die Nachprüfung bestätigte

| | |
|---|---|
| **Entflechtung** | K4 = `top_konten_verh − konten_verh` fällt bedingt (+0,0014 gegen Nullpunkt +0,0022). **K4 war K5.** Ein Fund, nicht zwei |
| **K5 bedingt** | trägt weiter (+0,0051 gegen +0,0024) |
| **Monotonie** | bei 6 h monoton über alle fünf Fünftel (+0,0004 → +0,0072) |
| **Beide Hälften** | beide tragen (+0,0081 / +0,0062) |

## 4.2 ⛔ Killer 1 — der Effekt liegt UNTER der Auflösung

**Trennschärfe, korrekt in eine neutralisierte Menge gepflanzt:**

| gepflanzt | Fundquote |
|---|---|
| **0,00** | **5 %** ✔ Anlage sauber geeicht (Sollwert 10 %) |
| **0,02** | **100 %** |
| 0,05 … 0,40 | 100 % |

➤ **Zuverlässig gefunden ab 0,02 R. Der K5-Effekt ist 0,0072 R — ein
Drittel davon.**

⚠️⚠️ **Mein erster Trennschärfe-Lauf war falsch:** gepflanzt wurde in die
**echten** Daten, die den Effekt schon enthalten. Bei Stärke null meldete
er +0,0072 und „gefunden" — gemessen wurde Effekt **plus** Pflanzung.
Korrigiert, und erst die korrigierte Fassung zeigt die Auflösungsgrenze.

## 4.3 ⛔ Killer 2 — auf der Betriebsmenge trägt es nicht (F-212)

| 6 h | Wirkung | Nullpunkt | | Stunden |
|---|---|---|---|---|
| frei | +0,0072 | +0,0041 | trägt | 20.763 |
| 50 % | +0,0128 | +0,0098 | trägt | 8.144 |
| **20 %** | +0,0110 | **+0,0120** | ⛔ **trägt nicht** | 2.048 |
| **5 %** | — | — | ⛔ **nicht messbar** | **0** |

⚠️ Bei 24 h trägt K5 noch bis 20 % — bei 6 h, dem eigentlichen
Hebelhorizont, **nicht**.

**F-212 ist dabei nicht interpretiert, sondern abgeleitet:**
`messnorm_auswahl.MENGEN` und `messe_beitrag_auf_auswahl.momentum250`
definieren die selektierte Menge als Top-Anteil nach der 250-Tage-
Entwicklung — genau die Größe, nach der `auswahl.py` im Betrieb rangt.

---

# § 5 ⭐⭐ Der eigentliche Befund — und meine erste Erklärung dafür war falsch

> **Auf der Menge, die die Kette durchlässt, ist kein Beitrag nachweisbar.**

⚠️⚠️ **KORRIGIERT auf Nutzerfrage** (*„prüfe ob Fehler in der Messung
möglich sind oder falsche Annahmen"*). Meine erste Fassung schrieb das der
Auswahlstufe zu (`K_GROSS = 2 von 43`). **Nachgemessen ist die Ursache eine
andere:**

| Symbole je Stunde im Querschnitt | |
|---|---|
| 5. Perzentil | **9** |
| **Median** | ⭐ **18** |
| Maximum | **45** |

**Nicht 116, wie ich angenommen hatte.** `konten_verh` liegt nicht für alle
Symbole zu jeder Stunde vor. 5 % von 18 sind **ein** Symbol — die
Mindestgrenze von vier Gewählten verwirft dann jede Stunde. Bei 20 % haben
nur **50,7 %** der Stunden mindestens vier.

## 5.1 ⚠️⚠️ Und das trifft JEDE Messung dieser Serie

**Aus 18 Symbolen werden Fünftel zu je drei bis vier Werten gebildet.**

| | |
|---|---|
| Das ist die Grundlage, auf der auch der K5-Hinweis stand | (§ 4) |
| Es erklärt den **positiven Nullpunkt** mit | der Median einer 3-Werte-Gruppe aus einer linksschiefen Verteilung ist systematisch verschoben |
| ⛔ **Was NICHT folgt** | dass die Messungen falsch sind — der gezogene Nullpunkt fängt genau diesen Bias ab. Aber die **Auflösung** ist dadurch grob, und das erklärt die 0,02 R |

➤ **Zwei Auswege, beide ungemessen:** mehr Symbole je Stunde (Terminmarkt-
Abdeckung prüfen) oder **Terzile statt Fünftel** — bei 18 Werten wären das
6 je Gruppe statt 3.

⚠️ **P-1 bleibt bestehen**, aber aus dem anderen Grund: die Auswahlstufe
rangt nach 250 Handelstagen für einen 6-h-Trade. Der Blindheitsbefund ist
ihr **nicht** zuzuschreiben.

---

# § 6 Was gilt und was nicht

| | |
|---|---|
| ⛔ **K5 `konten_verh` ist KEIN Befund** | der Hinweis aus A2 hält den Nachprüfungen nicht stand |
| ⛔ **K4 ist erledigt** | es war K5 |
| ⛔ **H-B (Stufen kalibrieren) entfällt vorerst** | es gibt nichts zu kalibrieren |
| ✔ **Die Messanlage ist geeicht** | 5 % Fehlalarm bei Stärke null, 100 % Fundquote ab 0,02 R |
| ✔ **A1 und der Modellfund bleiben** | drei Ausgänge gegen eine Zwei-Ausgänge-Formel |
| ⭐ **P-1 wird dringender** | nicht weniger |

## 6.1 Offen geblieben

- **out-of-sample** für die Stufen — nachrangig, scheitert an derselben
  Auflösungsgrenze.
- **K6 in Gegenrichtung** (durchweg negativ, −0,0133 bis −0,0004) — meine
  Prüfung testet nur auf „größer als Nullpunkt".
- ⚠️ **Das positive Vorzeichen von K5 ist unerklärt.** Die Vorabfestlegung
  erwartete **negativ** (einseitige Retail-Positionierung → Squeeze).
  Gemessen positiv. Eine Vermutung wäre hier kein Befund.

---

# § 7 Eigene Fehler in diesem Durchgang — beide vor dem Urteil gefunden

| | |
|---|---|
| **Trennschärfe in echte Daten gepflanzt** | hätte die Auflösungsgrenze verdeckt und K5 bestätigt |
| **H-A auf `frei` statt selektiert** | meine eigene Vorabfestlegung 10 § 5 schreibt F-212 vor. Nachgeholt — und es kippt den Befund |

⚠️ Dazu ein dritter, kleinerer: die Entflechtung lieferte bei zu wenigen
Symbolen still `nan`, was mein Code als „fällt bedingt" ausgab. **Nicht
messbar ist nicht gefallen** — behoben.

---

# § 8 ⚠️ Alle Annahmen dieser Messung — offen benannt

**Auf Nutzerfrage vom 25.09. systematisch durchgegangen.**

| # | Annahme | Lage |
|---|---|---|
| **A1** | ⚠️ **Der Querschnitt hat 18 statt 116 Symbole** | **FEHLER GEFUNDEN**, § 5 korrigiert |
| **A2** | „offen = Ausstieg zum Schlusskurs" | ⚠️ eine **Handlungsannahme**, keine Messung. Real würde man anders aussteigen (§ 2.1 des Vorlaufblatts: 21 % standen über 1 R) |
| **A3** | Stop aus dem **Tages**-ATR | ⚠️ bekannt zu weit für 6 h — **ausgewiesen, nicht behoben**. Die skalierte Variante lief mit |
| **A4** | nur **LONG** | ⚠️ Short ungemessen. Wirkt `konten_verh` dort umgekehrt, fehlt die Hälfte |
| **A5** | **Takt 6 h** bei Haltedauern bis 72 h | ⚠️ benachbarte Anker teilen bis zu 66 von 72 Stunden. Der Nullpunkt mischt **innerhalb** der Stunde, nicht über die Überlappung. ➤ Dass `KON zufall` sauber blieb, spricht dagegen — **schließt es aber nicht aus** |
| **A6** | **Median** als Statistik | bei 3–4 Werten je Fünftel verzerrt; der Nullpunkt fängt es ab, kostet aber Auflösung |
| **A7** | `momentum250` = 250 × 24 Stunden | ✔ korrekt — bei Krypto ist jeder Kalendertag ein Handelstag |
| **A8** | Fünftel **quer über die Symbole** | ✔ Konvention wie `marktrang`, nicht über die eigene Historie |

## 8.1 Die drei Fehler, die in diesem Durchgang gefunden wurden

| | gefunden durch |
|---|---|
| Trennschärfe in echte statt neutralisierte Daten gepflanzt | eigene Prüfung, vor dem Urteil |
| H-A auf `frei` statt selektiert (F-212) | eigene Vorabfestlegung, nachgeholt |
| **Querschnitt 18 statt 116** | ⭐ **Nutzerfrage** |

⚠️ **Der dritte wäre ohne die Nachfrage in einen registrierten Befund
gelaufen.**
