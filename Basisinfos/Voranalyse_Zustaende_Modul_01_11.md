# Voranalyse — Ebene-1-Modul `agent/zustaende.py` (Fütterung §6 Schritt 3, 01.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 01.11.):** *„ja, starte mit der Voranalyse – prüfen, gegenprüfen und doku“*.
**Gehört zu:** [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) (SF1–SF8, §4 Blöcke, §5 Takt, §6 Schritt 3) ·
[`Voranalyse_S1_Ergaenzung_01_11.md`](Voranalyse_S1_Ergaenzung_01_11.md) (die elf S1-Reihen, §6 Grundgesamtheit) ·
[`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) (Sichten S1–S8, Entscheidung A).
**Stand:** ✔ **entschieden a und gebaut 01.11.2026** (§7) — Nachweis 10 von 10, Prüfpaket 14 von 14. **Betrieb unberührt.** *(Vorlage-Stand:)* Geprüft nur lesend auf
`data/_sichten/sichten.db`, dazu zwei FRED-Abfragen (Veröffentlichungstermine).

---

## 0. Worum es geht

Die Satzform steht als **Probe** (`Rechenkern_02_10/fuetterung_satzform_probe.py`, 35 Zustände). Schritt 3 macht daraus **ein Modul**,
das live und im Rückspiel **derselbe Rechenweg** ist (SF8, Ü8), mit Prüfpaket. Bevor die Probe zum Modul wird, ist sie selbst
geprüft worden — mit **vier echten Fehlern** als Ergebnis (§2).

---

## 1. Umfang — was hinein gehört und was nicht

| | | Begründung |
|---|---|---|
| ✔ **Sicht-Zustände S1–S4, S7** | die 35 Zustände der Probe (S1 16, S2 6, S3 8, S4 4, S7 1) | Fütterung §1; S1 seit 01.11. vollständig |
| ✔ **S8 Termine** | FOMC, CPI, Arbeitsmarkt als **Termin-Fakt**: nächster Termin, Abstand, gemessener Faktor (`termin_fakt.FAKTOR_2H`) — **kein Rang** | Datenbasis Entscheidung A: *„S1, S2, S3, S4, S7, S8 sofort“*. S2 fragt ausdrücklich *„Welcher Termin kann das kippen?“* |
| ✘ **Asset-Zustände** (Fütterung §4 Block 2) | Kurs-Lage, REGEL0-Lage, Verwässerung, Wal, Bestand | Quellen liegen im **Betrieb** (NB); die Messung G7 *„Wert der Sichten“* braucht sie nicht. Folgt mit **G8** |
| ✘ **Ereignisse** | Rohmeldungen, Ankündigungen | kommen **nur** über den Ereignis-Leser A1 (Fütterung §3, G9) |
| ✘ **S5, S6** | KOSPI/Nikkei, Frankreich-Abstand | Quellen noch nicht nachgewiesen (Datenbasis §3) |

---

## 2. Befunde — die Probe geprüft und gegengeprüft

| # | Befund | gemessen | Folge |
|---|---|---|---|
| **Z1** | ⚠⚠ **Jahrgangsloch (Fehler).** `stand_am` lässt einen FRED-Jahrgang am Tag nach `bis` fallen — der Nachfolger ist aber erst **einen Tag später** bekannt (`bekannt_ab` = Folgetag der Veröffentlichung). An diesem Tag fehlen alle revidierten Beobachtungen, oft die **ganze Reihe** | 2025-12 bis 2026-10 (333 Stichtage): **M2 an 11 Tagen, NFCI an 48**, Dollar-Index an 2. Beispiel 24.02.2026: M2 **leer** | Regel: ein Jahrgang gilt **bis einschließlich `bis` + 1 T**. ✔ **Gegengeprüft:** alle **99.080** Jahrgangswechsel haben den Nachfolger **genau** bei `bis` + 2 T 00:00 — keine Überlappung, kein Rest. Mit der Regel: **0** verschwundene Beobachtungen, **nie** zwei gültige Jahrgänge zugleich |
| **Z2** | ⚠ **Absturz (Fehler).** Ist eine Reihe am Stichtag leer, bricht das Maß „gegen Vorjahr“ ab (`date_range` mit NaT) — die ganze Probe endet | am Lochtag 24.02.2026 **Traceback** statt 35 Zeilen | jedes Maß mit Leer-Prüfung; leere Reihe = eigene Zeile *„KEINE Werte vor dem Stichtag ⚠“* (gibt es schon, griff hier nicht) |
| **Z3** | **Season-Stufe mit FRED-Verzug.** Die Ampel datiert M2 mit **35 T** Verzug (`makro_lage.REIHEN`); tatsächlich erscheint ein Monat nach **40–59 T** (Median 55) und wird revidiert (B2-Schwelle 5 % in **2 von 64** Monaten anders) | Stufe jahrgangstreu nachgerechnet: B2 auf der anderen Seite der Schwelle an **73 Tagen**, die **Stufe an 0 von 2.454** Tagen anders — auch im Rückspielfenster 0 von 294 | **nichts zu ändern** für die Sicht. Vermerk für **P3** (Mail K1 ↔ Ebene 1): der 35-T-Verzug datiert M2 rückblickend rund 20 T zu früh |
| **Z4** | **Alter des Stands je Zustand sehr verschieden** — ein fester Grenzwert passt nicht | Median/P99 in Tagen: Krypto 1/1 · Aktien, Rohstoffe 1/4 · Zinsen 2/5 · NFCI 9/13 · Netto-Liquidität 5/8 · **M2 70/87** · GDELT 1/5 (max 18 = Juni-2025-Lücke) · **Breite/Stufe am Desktop bis 39** (Messbasis eingefroren 20.09.) | neue Regel **SF9** (§3): ⚠ *veraltet*, wenn das Alter über dem 99. Perzentil der **eigenen** Alter im Fenster liegt — abgeleitet, nicht aufgezählt |
| **Z5** | **Rang** ✔ | Probe = `scipy.percentileofscore(kind="mean")` an **20 von 20** Niveau-Zuständen (29.10.2026) | bleibt; im Prüfpaket als Vergleich |
| **Z6** | **Laufzeit** ✔ | 2,2 s je Stichtag samt Laden der Ablage (29 MB) | Rückspiel ≈ 330 Stichtage: Ablage **einmal** laden, dann je Stichtag rechnen |
| **Z7** | **S8 Termine — Quellen** | FOMC: `p59_termin_vorpruefung.FOMC` (2023–2025, mit **2025-12-10**) + `cycles.FOMC_MEETING_DATES` (2026/27) — **zwei Listen**. CPI/Arbeitsmarkt: FRED `release/dates` liefert **rückwirkend ab 2020** und **künftige** (CPI 88, NFP 86 Termine) | eine FOMC-Liste (cycles um 2020–2025 ergänzen, Quelle Fed). **[U]** 2025 verschob der Shutdown Termine (CPI 18.12., NFP 16.12.) — ob die Verschiebung am Stichtag schon **bekannt** war, liefert FRED nicht; im Rückspiel ab 01.12.2025 mit ⚠ |
| **Z8** | GDELT-Restlücken 2026 (≤ 6 T) lösen das Lücken-Kennzeichen nicht aus (Schwelle > 10 T) | Fütterung §8 | so lassen — eine Lücke unter der Aktualisierungs-Schwankung ist kein Befund; SF9 fängt einen **aktuellen** Ausfall |
| **Z9** | „200-T-Schnitt“ = 200 **Zeilen**: bei Krypto Kalendertage, bei Aktien/Rohstoffen Handelstage | Konvention der Märkte | so lassen, in der Lesehilfe **einmal** erklärt (wie P4) |

⚠ **Z1 und Z2 sind Fehler der Probe**, nicht der Daten. Die Probe-Ausgaben vom 31.10. und 01.11. (29.10.2026, 01.12.2025) sind **nicht**
betroffen — beides sind keine Lochtage (Wechsel M2 am 27.10. bzw. 23.12.). Im Rückspiel wären es **59 von 333 Tagen** gewesen.

---

## 3. Bauplan

**Ein Modul, nur lesend, ohne Netz:**

| Teil | was |
|---|---|
| `DEFINITIONEN` | die 35 Zeilen der Probe (Sicht, Quelle, Symbol, Name, Maß, Einheit, Lesart) — **aus der Probe verschoben**, nicht kopiert |
| `Ablage(pfad)` | lädt `sichten.db` **einmal** (`mode=ro`), verweigert die Produktions-DB |
| `stand_am(T)` | Jahrgang mit `bekannt_ab ≤ T` **und** (`bis` leer **oder** `bis` + 1 T ≥ Tag von T) — **Z1** |
| `zustaende(T, ablage, jahre=5)` | → Liste `Zustand(sicht, schluessel, name, wert, mass_wert, rang, klasse, stand, alter_t, kennzeichen, satz, auffaellig)` — **strukturiert**, weil der Takt (§5: *Klassenwechsel löst neues Gutachten aus*) die Klasse je Zustand vergleichen muss |
| `termine(T, ablage)` | S8: je Art der nächste Termin nach T, Abstand, Faktor — aus `sichten.db` (Quelle `termin`, `bekannt_ab` = Tag der Aufnahme in den Kalender, ⚠ Z7) |
| `zeilen(liste, sicht)` | die Textzeilen für den Prompt (Satzform SF1, ● nach SF3/SF6) |
| Probe | wird zur dünnen Hülle um das Modul — **dieselbe** Ausgabe |

**SF9 (neu, Fakt):** *„⚠ Stand N T alt (üblich ≤ M T)“*, wenn das Alter am Stichtag über dem 99. Perzentil der eigenen Alter im
5-J-Fenster liegt. Live zeigt das einen Quellenausfall, im Rückspiel eine Datenlücke — beides darf die Sicht nicht für heutig halten
(SF5 zeigt das Datum, aber nicht, dass es **ungewöhnlich** alt ist).

**Laden für S8:** FRED `release/dates` (CPI 10, Arbeitsmarkt 50) und die FOMC-Liste ab 2020 in `sichten.db` — **zwei Abrufe**, über
die bestehende Auftragsliste (Ü8). FOMC 2020–2022 fehlen in beiden Listen → aus der Fed-Seite (`fomccalendars.htm`, historisch) ergänzen.

---

## 4. Prüfen und gegenprüfen — was beim Bau nachgewiesen wird

**Prüfpaket `Zustaende`** (ohne Netz, Kunstablage):

| # | Prüfung |
|---|---|
| 1 | **kein Vorgriff**: eine Zeile mit `bekannt_ab > T` ändert nichts; eine Beobachtung ≥ Tag T zählt nicht |
| 2 | **Jahrgangswechsel ohne Loch** (Z1): Kunstreihe mit Revision — am Tag `bis` + 1 gilt der alte, am Tag `bis` + 2 der neue |
| 3 | **leere Reihe** → Zeile *„KEINE Werte“*, kein Absturz — für **jedes** Maß (Z2) |
| 4 | Fenster: ⚠ bei kürzer als 5 J, ⚠ bei Lücke > 10 T, ⚠ veraltet nach SF9 |
| 5 | **jede** Definition mit Rang hat eine Lesart; Kategorie ohne Rang und ohne ● (V5) |
| 6 | Klassengrenzen SF3; Rang = `percentileofscore(kind="mean")` |
| 7 | die Season-Codes aus `SEASON_CODE`, die Termin-Faktoren aus `termin_fakt` — **eine Quelle** |
| 8 | nie Produktions-DB |

**Nachweis gegen echte Daten** (Skript wie `s1_nachweis.py`):

| # | Gegenprobe |
|---|---|
| N1 | Modul = Probe **bitgleich** an 29.10.2026 und 01.12.2025 (keine Lochtage) |
| N2 | an den **59 Lochtagen** weichen **nur** FRED-Zeilen ab, und dort steht jetzt der Wert statt *„KEINE Werte“* / Absturz |
| N3 | ⚠⚠ **Vorgriff am Ergebnis**: je Stichtag Ausgabe mit voller Ablage = Ausgabe mit einer Ablage, die **nur** Zeilen mit `bekannt_ab ≤ T` enthält — an allen 333 Rückspiel-Stichtagen |
| N4 | alle 333 Stichtage laufen ohne Fehler; Laufzeit gemessen |
| N5 | S8: FOMC-Termine gegen die Fed-Liste, CPI/NFP gegen FRED an den Stichtagen; der gemessene Faktor = `termin_fakt` |

---

## 5. Was nicht berührt wird

Betrieb, NB, Mail, Season-Ampel, `makro_lage`. `sichten.db` liegt nur am Desktop; das Modul läuft am NB erst mit **G8**
(dort ist auch P3, der Abgleich Mail ↔ Ebene 1, und Z3 gehört dazu).

---

## 6. Zur Abstimmung — eine Frage

**Freigabe für den Bau nach §3–§4?**

| | Weg | Folge |
|---|---|---|
| **a** | **so bauen**: 35 Zustände + S8 Termine, Z1/Z2 behoben, SF9, Prüfpaket, Nachweis N1–N5 | ein Schritt; danach steht Ebene 1 für das Rückspiel vollständig |
| b | ohne S8, Termine erst mit A1 | weniger zu laden — aber S2 fragt nach dem Termin, und Entscheidung A sah S8 **sofort** vor |

**Empfehlung a.** Z1–Z9 und SF9 sind fachlich begründet und hier nicht zur Wahl gestellt — Einwände willkommen.

✔ **Entschieden 01.11.2026 (Nutzer: *„a, bauen – prüfen, gegenprüfen und doku“*)** — Ausführung in §7.

---

## 7. Ausführung und Nachweis (01.11.2026)

**Gebaut** — nur Desktop, Betrieb unberührt:

| Teil | was |
|---|---|
| `agent/zustaende.py` | `DEFINITIONEN` (die 35, aus der Probe verschoben), `Ablage` (einmal laden, `mode=ro`, Produktions-DB verweigert), `stand_am` mit der Jahrgangsregel **Z1**, `zustand` (Rechnung der Probe + **Z2** vor jedem Maß + **SF9**), `termine` (S8), `zustaende`, `zeilen`, `text`. Rückgabe **strukturiert** (`Zustand`: Satz, Klasse, Rang, Stand, Alter, Kennzeichen) |
| `Rechenkern_02_10/fuetterung_satzform_probe.py` | nur noch Hülle um das Modul — **ein** Rechenweg (SF8) |
| `api/sichten_quellen.py` | `termine_fred` (CPI 10, Arbeitsmarkt 50 aus FRED `release/dates`), `termine_fomc`, in **derselben** Auftragsliste. Zeile: Tag (New York), UTC-Sekunden, `bekannt_ab` = Termin − `TERMIN_VORLAUF_T` (90 T) |
| `agent/cycles.py` | `FOMC_ERKLAERUNG_2023_2025` (aus `p59`, dort gemessen) — **nicht** in `FOMC_MEETING_DATES`, der Betrieb liest die Liste unverändert |
| `pruefe_pakete.py` | Paket **Zustaende** (14, ohne Netz) · SichtenQuellen +1 (Termine, 14) |
| `Rechenkern_02_10/zustaende_nachweis.py` → `.txt` | N1–N5 gegen echte Daten |

**Geladen** (Sicherung `sichten_vor_zustaende_01_11.db`): Termine CPI 88 (2020-01-14 – 2026-12-10), Arbeitsmarkt 86
(2020-01-10 – 2026-12-04), FOMC 40 (2023-02-01 – 2027-12-08).

**Abweichung vom Plan §3:** FOMC 2020–2022 **nicht** nachgetragen. Ein Termin hat keinen Rang und kein Fenster — das Rückspiel ab
12/2025 braucht nur die kommenden Termine. Vor 2023 meldet S8 *„kein Termin bekannt ⚠“*, nie still.

**Unterwegs gefunden und behoben:**

| | |
|---|---|
| Shutdown-⚠ zuerst auch beim FOMC | falsch — verschoben wurden nur die **BLS**-Termine (CPI, Arbeitsmarkt); `SHUTDOWN_ARTEN` |
| **Z10** (Prüfpaket): hat die Stufe **nie** gewechselt, nannte die Probe als „seit“ den **letzten** Tag | jetzt der erste. In den echten Daten trat es nicht auf (die Stufe wechselt ab 2020 mehrfach) |

**Nachweis** (`zustaende_nachweis.txt`, **10 von 10 grün**):

| # | Ergebnis |
|---|---|
| N1 | Modul = alte Probe (aus Git, `ceb7df73`) an **01.12.2025 und 29.10.2026: je 35 von 35 Zeilen** gleich — einziger Zusatz SF9 an 2 Zeilen (Breite, Season-Stufe am 29.10.: *„⚠ Stand 39 T alt (üblich ≤ 20 T)“*, die eingefrorene Desktop-Messbasis) |
| N2 | 333 Rückspiel-Stichtage (01.12.2025 – 29.10.2026): **0** leere FRED-Zeilen (alte Regel: 59 Lochtage), **kein** Stand läuft rückwärts |
| N3 | ⚠⚠ **Vorgriff am Ergebnis: 0 von 333** Stichtagen verschieden zwischen voller Ablage und einer Ablage, die nur das am Stichtag Bekannte enthält (`bis` nur, wenn der Nachfolger schon bekannt war) |
| N4 | 0 Fehler; 1.532 s für 333 Stichtage × 2 ≈ **2,3 s je Rechnung** |
| N5 | FOMC in der Ablage = `agent.cycles` (40); CPI = FRED (88 = 88); Arbeitsmarkt = FRED (86 = 86); nächster FOMC je Stichtag unabhängig nachgerechnet: **0 von 333** falsch |

**Probe 29.10.2026** (neu geschrieben): 35 Zustände, 13 auffällig, ≈ 1.760 Token; dazu S8 drei Zeilen (≈ 235 Token) — Arbeitsmarkt
in 8,6 T, CPI in 12,6 T, FOMC in 41,8 T.

**Was offen bleibt:** S8 hat keine Klasse — wann ein Termin ein neues Gutachten auslöst (Takt §5), regelt der Ereignis-Leser A1
(G9). Das Modul läuft am NB erst mit **G8** (dort liegt `sichten.db` noch nicht).
