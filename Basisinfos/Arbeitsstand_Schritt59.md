# Arbeitsstand Schritt 59 – lebende Übergabe

**Zweck:** Ein Sitzungswechsel soll jederzeit ohne Vorbereitung möglich sein (Nutzerentscheidung 17.09.2026: Sitzung stabil halten, Übergabe parallel mitziehen, Probelauf einer neuen Sitzung nach Phase 0). **Aktualisiert am Ende jedes Pakets.**

**Stand:** 24.09.2026 · ⛔ Hebelumbau ABGESAGT - B0 zeigt, die Wirkung kam aus dem gesperrten Fuenftel (2.576); Schritt A bleibt (2.575) · zuvor 20.09.2026 · letzter Commit `1b743e3` (**A1 gefallen** – die Messanlage ist auf `barriere` geeicht) · Prüfsuite **3081 Prüfungen, 3 rot** (alle im Paket `Neuaufnahme`, reiner Desktop-Datenstand, kein Codefehler)

**Am Notebook:** letzter Pull `7490586` (schlanke Diagnose) · Laufzeitcode aus `02eca50` (terminmarkt-Protokoll) und `f92205f` (Laufzeitwächter) ist **gepullt und neu gestartet**. ⚠️ Für den nächsten **Export** ist **kein Pull nötig** – die schlanke Diagnose liegt seit `7490586` dort. `1b743e3` enthält **keinen Laufzeitcode** (Messskript, Befunde, Dokumente).

## Zuerst lesen (in dieser Reihenfolge)

1. Memory `feedback_arbeitsliste_fehler_und_ablauf.md` – Ablauf je Paket und die Fallen, die schon passiert sind
2. `Basisinfos/Plan_Schritt59_Gesamtkette_17_09.md` – der abgestimmte Plan (§ 1 Bewertungsstand, § 1a Krypto zuerst, § 3/3a LLM-Rollen und Basisdokumente, § 6 Phasen, § 6a Stillstand, § 8 Entscheidungen)
3. Memory `project_schritt59_gesamtkette_messen.md` und `project_ausstehende_nb_kontrollen.md`
4. `Basisinfos/Rollout_Notebook_14_09.md` – was am Notebook woran zu erkennen ist

## ⭐ Das Ziel: Meilenstein M1 — Krypto-Einstieg investierbar

**Nutzerdefinition 18.09.:** technisch stabil · fachlich gemessen · rudimentäre Wirksamkeit belegt — **dann** wieder investieren. Priorität: der **Einstieg** (Spot, Hebel, Akkumulation), durchgängig über deterministische Komponenten **und** LLM. Sieben Abnahmekriterien in `Plan_Schritt59` § 11, als Vorgabe `M1-KRYPTO-EINSTIEG` in `soll_ist`.

⚠️ **Der Engpass ist das LLM-Kontingent** (2.459-llm-budget): 500/Tag je Modell, der Betrieb braucht im Mittel 245 (Spitze 565 — über der Grenze). Ohne Produktionsstillstand ist die LLM-Messung nicht planbar. Zuerst ein **Kalibrierlauf** (50 Anker, halber Stillstandstag), dann wird der Hauptlauf dimensioniert (**N13**).

**Weg:** ~~Phase 3 (Spot)~~ → **Phase 4 (Hebel)** → Phase 8 gepaart (A/B/Zufall) → Phase 9 → Schritt 60 → Abnahme M1. Akkumulation läuft parallel. **Nicht** auf dem Weg: Ausstieg, Nicht-Krypto, Multiasset.

### ✔✔ STAND 23.09.2026 — PHASE 3 IST DURCH, PHASE 4 IST DER NÄCHSTE SCHRITT

| Phase-3-Punkt | |
|---|---|
| `turnover` einzeln | ✔ reproduziert → **TRÄGT** (2.535) — und das Urteil kippt wegen der **Trennschärfe**, nicht des Beitrags |
| die Kette | ✔ reproduziert (0,5 %) → **TRÄGT** auf beiden Quellen (2.537) |
| N-67 (`schnitt` über die Kette) | ✔ **TRÄGT zusätzlich**, beide Quellen (2.538) |

⚠️ **Was Phase 3 NICHT geliefert hat:** einen belegten Qualitätsgewinn des
Nennerwechsels. Der gepaarte Test kommt auf +0,0479 R bei einer
Trennschärfe von 0,100 R — **nicht belegt**. Das ist kein Widerspruch zum
Umbau: S6 war ausdrücklich ein **Abdeckungs**paket.

➔ **Nächster Schritt: Phase 4, und dort der eine offene Punkt** — der
Hebelfaktor unter der **jetzigen** Konfiguration. 2.533 hält fest: *„die
Simulation lief auf der ALTEN Schwelle; unter 0,060 ist der genaue Faktor
offen"*. Das ist M1-Kriterium 2 (*Zielzone 2–5x belegt*).

## ⚠️⚠️⚠️ STAND 24.09.2026 — DER HEBEL SOLLTE SEINE EIGENE BEWERTUNG BEKOMMEN — ⛔ B0 HAT DAS GEKIPPT

**Vor Phase 4 hat sich die Lage geändert.** Nutzerthese, belegt (2.571):
*„HEBEL und SPOT sind dasselbe — das ist FALSCH."*

| | |
|---|---|
| **Die Ursache** | 2.490 („kein Beitrag trägt auf `barriere`") lief auf **H20**. Die echten Hebelpositionen haben eine **Median-Haltedauer von 0,30 Tagen** (2.493) |
| **Schritt 1** ✔ | `HORIZONT_JE_LAGE` steht in der Norm, beide Messanlagen warnen (2.572/2.573) |
| **Schritt 2** ✔ | 2.490 auf **H3** wiederholt. **R-R11 bitgleich reproduziert.** `oi_aenderung` **+0,0069 [+0,0031 … +0,0108]**, Kontrolle sauber, Saatprobe bestanden (2.573) |
| **Entscheidung** | ✔ nach der Vorabfestlegung: **der Hebel bekommt seine eigene Bewertung** |

### ⛔⛔⛔ NACHTRAG SELBER TAG: **B0 hat den Umbau gekippt** (2.576)

Pflichtschritt **B0** ist gelaufen. Ohne das von Stufe 6 gesperrte oberste
Fünftel fällt `oi_aenderung` von **+0,0069 [+0,0031…+0,0108] TRÄGT** auf
**−0,0002 [−0,0032…+0,0030] trägt nicht**. R-R11 vorher bitgleich,
Kontrolle in beiden Läufen sauber.

> **Die Wirkung kam aus dem Fünftel, das die Kette nie sieht.
> Der Umbau entfällt.**

⚠️⚠️ **Und der Nebenbefund wiegt schwerer: es fallen ALLE VIER.**
funding +0,0002→−0,0005 · turnover +0,0040→+0,0021 · schnitt
+0,0066→+0,0003. **Das oberste OI-Fünftel ist der Ort, an dem die
Trennkraft sitzt — und genau den sperrt die Kette weg.**

➤ Offene **Messfrage** an Stufe 6 (betrifft auch `spot × einstieg`,
also M1-Kriterium 1): **Nutzerentscheidung**, bevor daran gearbeitet wird.

✔ **Schritt A bleibt** und trägt eigenständig (2.575).

### ⭐⭐⭐ DAS VORGEHEN FÜR DEN HEBEL — Kapselung, dann GEOMETRIE, dann Quote

Plan: **`Basisinfos/Bauplan_Hebel_einpflanzen_24_09.md`** · Befund **2.578**

**Die Rechnung, die die Reihenfolge erzwingt:** Kelly wird null bei
`q₀ = 1/(1+CRV) = 0,3333`. Gemessen auf H5 liegt q bei **0,284…0,323** —
es fehlen **1,03 bis 4,93 Prozentpunkte**. Beiträge liefern **0,21 Pp**
einzeln, **0,24 Pp** zusammen. ⛔ **Faktor 4 bis 21 zu wenig.**

> **Die Quote kann den Hebel nicht retten — es ist keine Frage der
> Messgenauigkeit, sondern der Größenordnung.**

⚠️⚠️ **Der Horizont ist eine ACHSE, keine Vorgabe** (Nutzerhinweis): H3 war
ein Beispiel. Gemessen wird über **2/3/5/10/20** — das Ergebnis *begründet*
`HORIZONT_JE_LAGE`, statt daraus zu folgen. 2.435 lief auf H5/H10/H20,
H2/H3 fehlen ganz.

⭐⭐ **Der Hebel stirbt nicht an Stundendaten:** jede Phase läuft auf
Tagesdaten. Der Pfad-Vorbehalt wird über die Horizontachse **gezählt** —
damit sagt die Messung selbst, ab wann Tagesdaten nicht mehr tragen.

✔ **Werkzeuge stehen:** `messe_stopweite_historisch.py` kennt `--horizont`
bereits, keine Änderung nötig.

**Kapselung K1→K2→K3** (Reihenfolge zwingend): `instrumente=()` heißt „gilt
überall" — **der Hebel erbt heute jeden Spot-Beitrag durch einen
Vorgabewert.**

### ⭐⭐⭐ RICHTUNGSENTSCHEID 24.09. — DREI GESCHÄFTE, DIE LAGE IST EINGANG

**Nutzerentscheidung:** *„Spot bleibt vorerst als eigener offener Punkt.
Und Hebel muss neu gedacht werden."* · **Reihenfolge: 1. Hebel ·
2. Akkumulation · 3. Spot.**

Konzept: **`Basisinfos/Konzept_Hebel_als_eigenes_Geschaeft_24_09.md`** ·
Befund **2.577**

| Lage | entsteht aus | Signale |
|---|---|---|
| `spot × einstieg` | **Vorgabe** — Rückfall für alles | 3.513 |
| `spot × akkumulation` | ✔ **Nutzerschalter** (`dca_erlaubt`) | 0 |
| `hebel × einstieg` | ⛔ **der Geometrie, nachträglich** | 0 |

> **Die Lage ist EINGANG, nicht AUSGANG.** Die Akkumulation ist das
> **Vorbild** (gewollte Lage), der Hebel ein **Ergebnis**.

✔ **Ohne massiven Umbau möglich:** `assetklassen.py:167` iteriert bereits
über `INSTRUMENTE_JE_GRUPPE` — die Schleife muss nur über **Lagen** laufen.
Und der LLM-Prompt ist für Spot/Hebel **bitgleich** (gemessen), die teure
Ressource muss also nicht verdoppelt werden.

⛔ **Verworfen:** Verzweigung im Lauf (Trichterzähler-Umbau) · Kette zu
100 % auf Hebel (schneidet die Verkaufsseite ab).

⚠️⚠️ **M1-Kriterium 2 ist nicht erfüllbar**, solange der Hebel kein eigenes
Geschäft ist. **M1 in seiner heutigen Definition ist kein Nahziel mehr** —
Nutzerentscheidung offen.

### ⛔⛔ Die vier Blocker — sie bleiben gültig für jede Instrumenttrennung

Plan: **`Basisinfos/Umbauplan_Hebel_eigene_Bewertung_24_09.md`** · Befund **2.574**

| | |
|---|---|
| **A** ⛔⛔ | **Das gemessene Fünftel 4 erreicht die Bewertung nie.** Trichterstufe 6 (`terminmarkt`) sperrt bei `oi_fuenftel >= 4` hart (`rollen_lauf.py:1608`) — genau für `einstieg` ohne Bestand, also die Hebel-Lage. 2.573 maß über **alle fünf** Fünftel. **Ob der Beitrag auf 0–3 noch trägt, ist ungemessen** → Pflichtschritt **B0**, und er kann den Umbau **kippen** |
| **B** ⛔ | **`instrument` ist bei der Quotenrechnung immer `spot`** (`rollen_lauf.py:2165`; der Quelltext sagt es wörtlich). Ein Beitrag mit `instrumente=("hebel",)` griffe **nie**. Heute wirkungslos, weil kein Beitrag das Feld setzt — **die Falle schlägt erst beim Umbau zu**. Lösbar mit einer Zeile |
| **C** ⛔⛔⛔ | **Ein Gleichheitswächter (`:2591`) verbietet genau diese Trennung** — er meldet einen Fehler, sobald Hebelquote und Bewertung abweichen. Sobald B gelöst ist, feuert er bei **jedem** Signal. ⚠️ **Nicht entfernen** — er schützt vor echtem Auseinanderlaufen; sein **Bezugspunkt** wird lagerichtig |
| **D** ⚠️ | **Drei** Stellen rechnen die Bewertung (`:2162`, `:2579`, `:1192`), alle mit `instrument`. ⚠️ `:1192` entscheidet nichts, ist aber **die Messspur** — bliebe sie auf `spot`, wäre der Umbau **im Betrieb nicht nachmessbar** |

### Die Ablaufkette — gegengeprüft, kein weiterer Blocker

**LLM-Rollen** (Stufe 8) liefern **vor** der Bewertung (Stufe 12) und kennen
sie nicht (2.398) → **der Umbau wirkt dort nicht**, die Lücke gehört in
Block **L-ROLLEN** (*D vor L*). **Strategien:** nur `hebel × einstieg`
betroffen, `spot × einstieg` unberührt. **Empfehlungen:** zwei Quoten
heißen zwingend **zwei Schwellen** (R-R9); die Mail muss beide ausweisen.


## ✔✔✔ A1 ist gefallen — der Hebel ist messbar

**2.485-a1-gefallen (20.09.):** die Messanlage ist auf `barriere` geeicht. **1 von 100 Fehlalarmen auf BEIDEN Zielgrößen** (Sollwert 5 %). Drei unabhängige Wege: Blocklänge unauffällig (±0,03), die Überschlagsrechnung aus 2.238 teilte durch √Blöcke statt √Tage, und `zufall` auf `barriere` **trägt heute nicht** (+0,0008 R). 2.238 ist auf **abgelöst** gesetzt.

⚠️ Die Anlage ist eher **übervorsichtig** (1 % statt 5 %) — das erklärt mit, warum so wenig trägt. ⚠️ Und **warum** die Messung am 09.09. anders ausfiel, ist **nicht geklärt**; ich stelle keine Vermutung als Erklärung hin. Paket A1Eichung 12/12, 10 Mutationen.

➔ **Phase 4 Punkt 2 ist frei**: Hebel-Einstieg auf `barriere`, r(q)-Simulation, *derselbe Trade als Spot*.

## ✔✔ `schnitt` rechnet wieder — und das Notebook kann ihn jetzt auch

⚠️⚠️ **Gefunden auf Nutzerfrage nach den Zusatzdatenbanken** (2.486-schnitt-tot): `marktrang.schnitte()` gab seit dem **18.09.** **null** Symbole zurück — die Messbasis war 12 Tage alt, die eingebaute Grenze liegt bei 10. Gemeldet wurde das nur ins Log; `datenfrische` kannte `messdaten.db` als Quelle **gar nicht**.

✔ **Aufgefrischt** (2.487-auffrischung): 493 Paare, 348 brauchbar, 544.136 Kerzen, 271 s. Vorher gesichert nach R-R11 (`messdaten_vor_auffrischung_20_09.db`). `schnitte()` liefert jetzt **537** statt 0; die Suite nennt Krypto nicht mehr als veraltet.

✔ **Schnitt-Job gebaut** (2.487-schnittjob, Nutzerentscheidung *„C ist die einzige brauchbare Variante“*): `betriebsreihen_job` holt die Reihen **täglich 03:30 UTC** selbst von Binance — **146–325 s** Erstbefüllung, **rund 167 s** Nachlauf, **30 MB** statt 1,5 GB, Gewicht 493 gegen 2.400/Minute. Paket Betriebsreihen 17/17, 16 Mutationen.

⚠️⚠️⚠️ **Die Trennung** (Nutzervorgabe *„die Trennung ist erforderlich“*): die NB-Datei trägt die Marke `_nur_betrieb`, und `lade_reihen_aus_db` **bricht ab** — dort gehen **32 Messskripte** durch. Dazu zwei Riegel am Erzeuger. Festgehalten in CLAUDE.md, Regelwerksmanual § 6 und Memory `feedback_betriebskopie_ist_keine_messbasis`.

⚠️✔✔ **Grundgesamtheit gelöst 20.09.** (2.487-grundgesamtheit) — und sie war nie eine Entscheidung, sondern eine **Messung** (Nutzerhinweis: *„ist das eine Entscheidung?“*). Gemessen: nur `TRADING` verschob **18 von 31** Kettenfünfteln, alle nach unten, weil die 167 Fehlenden im Median 65 % **unter** ihrem Schnitt liegen — der **Boden** der Verteilung. Nach dem Umbau (beide Zustände · Aufbewahrung **je Symbol** · Mindestlänge **400** statt 220): **0 von 29**, über alle Werte 0,8 % statt 52,6 %. Paket Betriebsreihen 23/23. ⚠ Kosten: 705 Paare, ~230 s, 40 MB. ⚠ **Laufzeitcode — NB braucht Pull und Neustart.**

⚠️ **Drei eigene Fehler, alle von der Prüfung gefangen:** `DB` statt `db` (NameError zur Laufzeit, derselbe wie im Laufzeitwächter), `SystemExit` fällt nicht unter `except Exception` (hätte den Scheduler-Thread mitgerissen — am Desktop bei **jedem** Lauf), und `sys.stdout.reconfigure()` gibt es als Dienst nicht.

⚠️ **Laufzeitcode: NB braucht Pull UND Neustart**, danach **K27**.

## ✔ Betriebsvorfall 20.09. — die Netzaussetzer sind erklärt

**Es war die Diagnose, nicht der Pull** (2.484-ursache). Der Nutzer hat es getrennt geprüft: *Pull ohne Diagnose blieb ruhig*. 295 MB Upload auf einen Drive-Ordner sättigen die Leitung; die Abrufe der laufenden Anwendung scheitern am 15-Sekunden-Zeitlimit — Terminmarkt 4/43, +48 Jobfehler.

✔ **Gebaut** (2.484-schlank): Diagnose **schlank als Vorgabe** (~8 MB statt 295), `--voll` für Messskripte, Lesehelfer mit lesbarer Meldung, drei Wächter gegen das Vergessen. Paket Diagnoseumfang 20/20, 9 Mutationen · ⚠️ **kein Laufzeitmodul** — Pull genügt, kein Neustart · ⏳ **K26**: ist die nächste Diagnose rund 8 MB, und bleiben die Timeouts aus?

## ⚠️ Betriebsvorfall 19.09. — sechs Stunden Stillstand

Die Anwendung war **14:06–20:29 lokal** weg (2.482-stillstand). Vier Spuren brechen im selben Fenster ab; die letzte Protokollzeile ist ein **erfolgreich** beendeter Job — kein Fehler, kein Traceback. Der Prozess wurde **von außen** beendet.

⛔ **Die Ursache wird NICHT weiter verfolgt** (Nutzerentscheidung 20.09.: *„streiche den Punkt mit Windows Ereignisprotokoll, das prüfe ich nicht“*). Der Stillstand bleibt damit **unerklärt** — der Laufzeitwächter meldet den nächsten, die Ursache des einen vom 19.09. bleibt offen. Der Nutzerhinweis auf einen **Netzwerkausfall am Nachmittag** erklärt die Timeouts, aber **nicht** den Stillstand — möglich ist eine gemeinsame Ursache (Ruhezustand).

✔ **Gebaut**: Laufzeitwächter im `staleness_watchdog` (2.482-waechter, Schwelle 45 min, eine Meldung je Lücke, Spur in `api_health`) · Marktrang-Zähler in der Diagnose (2.482-marktrang) · Paket Laufzeitwächter 12/12, 9 Mutationen · ⚠️ **Laufzeitcode: NB braucht Pull UND Neustart**, danach **K25** (kommt beim nächsten geplanten Neustart eine Stillstandsmail?)

## Wo wir stehen

| Paket | Stand |
|---|---|
| **Phase 3 Punkt 3 – Stufe `auswahl`** | ⛔ **gemessen 19.09.** (2.479): keine Zelle trägt; bei H20 ist die Anlage zu grob (0,40 R), bei H5 löst sie auf und die Wirkung liegt darunter. ➔ Mengensteuerung, kein Qualitätsfilter. ⚠️ Zwei eigene Aufbaufehler gefunden (2.479-eigene-fehler: Träger filterte die Ankermenge, Bezug waren alle statt der Wählbaren). Paket Auswahlstufe 10/10, 10 Mutationen · ✔ **`entscheider` gemessen** (2.480): **+0,2137 R → TRÄGT**, auch gegen die strengere Nullwelt aus den Bewertbaren; Datenlagenanteil +0,0461 R; 8 von 8 CRV-Werten. Paket Entscheiderstufe 12/12, 10 Mutationen · ✔ **`terminmarkt` belegt** (2.481): Größe registriert, **Stufe im Betrieb fast wirkungslos** (4 von 508 Zeilen) und **nicht protokolliert**. Paket Terminmarktstufe 6/6, 7 Mutationen · ✔ **Punkt 3 vollständig** · ⏳ offen: Punkt 5 (die vier ungemessenen Größen) · ✔ **Umsetzung gebaut 19.09.**: `terminmarkt` in `PROTOKOLL_IMMER` **und** in `NUR_EINMAL_JE_TAG` (höchstens eine Zeile je Symbol und Tag) · ⚠️ **Laufzeitcode: NB braucht Pull UND Neustart**, danach Export und Kontrolle **K21** (steht eine `terminmarkt`-Zeile in `zellen_lauf`, oder bleibt sie zu Recht leer?) |
| **Phase 3 Punkt 5 – die vier ungemessenen Größen** | ✔ **erledigt 20.09.** (2.483): `referenz_spy` **nicht trennbar** — im Querschnittsrang **rangidentisch** mit der reinen Kursrendite (0,999999), der Marktabzug kürzt sich weg. `fundamental_wachstum` → Multiasset. `stablecoin_kapital` und `optionsmarkt_dvol_skew`: **34 Punkte**, Warten hülfe bis 2029 → **Historie beschaffen** (Schritt 65). Paket Referenzstärke 9/9, 8 Mutationen · ✔✔ **PHASE 3 IST DAMIT VOLLSTÄNDIG** |
| Plan, Entscheidungen N1–N11, D1–D4 | ✔ abgestimmt |
| 0.6 Sperrzeiten am NB | ✔ belegt (Krypto 12 h, gehebelt ab 2x 3,5 h, Multiasset 24 h, G = Z.ai) |
| 0.8 Stillstand und Abgrenzung (Recherche) | ✔ Befunde 2.456-llm-pause, 2.456-etf-knopf, 2.456-abgrenzung |
| 0.9 ETF-Knöpfe gesperrt | ✔ gebaut `e45aa26` · am NB aktiv · ⏳ K13 Oberflächenblick (Nutzer) |
| 0.7 + 0.10 Kennzeichnung und `signals.gruppe` | ✔ gebaut `03e5724` · am NB: Spalte da, Drift leer, keine Fehler · ⏳ K14 erste gekennzeichnete Mail |
| 0.4 Messskripte nur lesend (E1: alle acht) | ✔ gebaut (2.457-nurlesend) · Paket NurLesend 18/18  · ✔ Restpunkt 18.09. erledigt (beide Skripte `mode=ro`) |
| 0.3 Protokollfehler Messnorm (`null_ziehungen`) + CLAUDE.md (E2) | ✔ gebaut (2.457-protokoll) · Messstandard 29/29  |
| 0.2 Befunde W1–W11 | ✔ erledigt: 2.457-w1 … w9 neu, dazu 2.457-n2 (Rahmen-Sätze erreichen BC, sprechen ab ca. Mitte Oktober → Entscheidung N12) und 2.457-n3; W10/W11 als Nachtrag |
| 0.5 Plan bereinigen | ✔ erledigt: A9 entwirrt, 37 fertig, 42 im Titel, 43/25 Rückverweis, R-R12, 2.414 als Hinweis, KRYPTO-ZUERST offen |
| 0.2b Basisdokumente | ✔ erledigt: Landkarte an fünf Stellen korrigiert, Manual **nur** Standvermerk (Weg A, Schritt 58), Anforderungen Z. 697, zwei Konzeptdokumente mit Standvermerk |
| 0.12 Mail-Abschnitte „Umfeld“/„Zusatzinfo“ (2.457-w3) | ✔ gebaut · Paket Mailabschnitte 18/18 · `bc_ein` bitgleich · ⏳ NB: Pull **und Neustart**, dann K16 |
| 0.13 Datenarchäologie | ✔ erledigt (2.458-archaeologie, 2.458-fallzahl): Trichter seit 14.08. vorhanden, **Potential nicht rekonstruierbar**, laufender Prompt-Stand nur 24 entschiedene Fälle |
| **Phase 1 Teil 1** (1.7 + 1.2 + 1.3) | ✔ gebaut (2.458-protokoll-1): Kurs an allen drei Schreibwegen, Potential auch bei durchgelassenen, neue Spalte `phase` · Paket Protokoll 15/15, 8 Mutationen rot · ⏳ NB: Pull **und Neustart**, dann K17 |
| **Phase 1 Teil 2** (1.1 Spur je Zelle) | ✔ gebaut (2.458-protokoll-2): neue Tabelle `zellen_lauf`, Filter ab `urteil` + `auswahl`, ~193 Zeilen/Tag · Paket Protokoll 29/29, 8 Mutationen rot · ⏳ NB: Pull **und Neustart**, dann K18 |
| **Phase 1 Teil 3** (1.4 Führung, 1.6 Sperre) | ✔ gebaut (2.458-protokoll-3): Tabelle `fuehrung_lauf` mit Empfehlungen **und** Vergleichsarm; gesperrte Akkumulation höchstens eine Zeile je Tag · Paket Protokoll 42/42, 10 Mutationen rot · ⏳ NB: Pull **und Neustart**, dann K19 |
| **Phase 1 Teil 4** (1.5 Ausstiege) | ✔ gebaut (2.458-protokoll-4, schließt 2.401): zwei Horizonte, richtungsbereinigt, rückwirkend – 224 von 611 Ausstiegen sofort gemessen · Paket Protokoll 55/55, 10 Mutationen rot · ⏳ NB: Pull **und Neustart**, dann K20 |
| **Phase 2** Live-Zählung | ✔ Werkzeug gebaut (2.459-zaehlung): `zaehle_kette.py`, 6 Sichten · Paket Zaehlung 11/11, 7 Mutationen rot · ⏳ vollständiger Lauf nach K19/K20 |
| **Phase 3** Schritt 1+2 | ✔ Reproduktion (2.460-repro) · Normurteil einzeln (2.460-norm: nur `oi_aenderung` trägt) · **Kette TRÄGT** (2.460-kette, +0,0403 R gegen Nullpunkt +0,0048) · ⏳ offen: Beitrag je Stufe (auswahl, terminmarkt, entscheider), die vier ungemessenen Größen |
| **Phase 3** Wiederholungssperre | ✔ **gemessen 18.09.** (2.461-sperre): **keine Länge trägt** – 1/2/3/5/10/20 Tage alle unter dem Nullpunkt ihrer eigenen Nullwelt; Kosten 43 % bis 87 % der Anker. ⚠️ 3,5 h und 12 h sind **nicht messbar** (Tagesraster, 2.461-sperre-auflösung). ✔ **Uhr je Zelle gebaut** (S1, 2.462-uhr-getrennt) – heute folgenlos (keine `akkumulation`-Signale), wirkt ab deren Freischaltung; dabei gefunden: Fail-soft war stumm (2.462-fail-soft). ✔ **S3 gemessen** (2.464-warten): Warten kostet nichts (Median 0,0000 R bis 24 h, Positivkontrolle findet 0,02 R); Streuung wächst auf 0,113 R nach 12 h. ⚠️ Unterdrückung vermessen (2.464-unterdrückung): `wiederholung` 39 %, `anlass` 32 %, `auswahl` 26,5 % – nur die erste ist eine Uhr. ✔ **`anlass`-Schwelle gemessen** (2.465-anlass): RUHIGER, aber schwach (10–15 %); Volumen −60 % bis −89 % (2.465-volumen). ✔ **Hochrechnung** (2.466): heute 84 Modellzellen/Tag von 500 Kontingent; ohne Sperre 2.257. ⚠️ Annahme hält nicht, Zahlen sind Untergrenzen (2.466-annahme); Live-Auswahl ist **k = 2** plus Bestandsdurchlass, nicht 20 %. ⛔ **S3 zurückgestellt** (2.467-verkauf-blockiert): die Sperre ist heute die einzige Bremse der ungemessenen Verkaufsseite. ➔ **Paket V** (Plan § 12): ✔ **V0 gebaut 19.09.** (2.469), ⛔ **V1 zurückgestellt** (2.471), ✔ **V2 gemessen 19.09.** (2.470: H5 −0,2518 R, Band schließt die Null aus — der Kurs steigt nach den Ausstiegen; nach Schwäche verkauft ist am schlechtesten), ✔ **V2b erledigt** (2.472: Zielgröße für V3 = **verkauft gegen behalten**, nicht Timing), ✔ **V3a gemessen und geklärt** (2.473 + 2.474): auf der **eigentlichen** Haltefrage (38 von 81 Werten, heute nicht mehr in der Auswahl) trägt nur `funding` — V3b darf sich nur darauf stützen, ✔ **V3b-1 gemessen** (2.476): `funding` als Verkaufsregel trägt auf der **ganzen** Haltemenge (+0,0791 R) und dort, wo der Wert noch in der Auswahl steht (+0,0824 R) — auf der **eigentlichen** Haltefrage **nicht trennbar** (+0,0178 R, Band fehlt 0,0019). ✔ **V3b-1b gemessen** (2.477): B1/B2/B3 — **keiner** schließt das Band; die beiden TRÄGT-Urteile fallen an der **Saatprobe** (1 von 5 bzw. 4 von 5). ➔ **Weg A ist entschieden, weil gemessen**: V3b-2 baut auf der ganzen Haltemenge mit Vorbehalt. ⛔ **PAKET V GESCHLOSSEN 19.09.** (2.478): V3b-2 und **V4** gehen an Schritt 43, **nach M1** — § 11.1 führt den Ausstieg unter *nicht in M1*, und der Blocker aus 2.467 ist mit V0 erledigt. ⚠️ V4 ist der größere Teil: von vier Verkaufsfällen ist **einer teilweise** bewertet |
| **Ungemessene Größen in der BC-Eingabe** | ✔ eingeordnet (2.459-ungemessen): vier Größen nie gemessen – zwei stumme jetzt gefiltert (folgenlos), zwei laufende unangetastet bis nach der Basislinie; alle vier als Kandidaten registriert, Messung in Phase 3, Entscheidung in Schritt 33 |
| 0.11 Pausenschalter nur für Modellaufrufe | offen, erst vor Phase 8 |
| Phase 1 Protokollierung | danach – eigene Voranalyse |

## Als Nächstes

1. ⏳ **NB-Export (schlank) – er ist zugleich Kontrolle K26.** Nach dem Export zuerst: ist die Diagnose **rund 8 MB statt 295 MB**, stehen die **Timeouts** still, und trägt sie das Feld `diagnose_umfang`? Danach in dieser Reihenfolge **K21, K25, K16, K6, K11a**.
2. ⏳ **Entscheidung des Nutzers offen: Phase 4 Punkt 2, Vorschlag E1–E5** (Hebel-Einstieg auf `barriere`, r(q)-Simulation, *derselbe Trade als Spot*). Ohne diese Antwort wird nicht gebaut.
3. Danach **Phase 4** weiter → Phase 8 gepaart (A/B/Zufall) → Phase 9 → Schritt 60 → **Abnahme M1**.

### Erledigt (Chronik)

1. ✔ **NB-Export 18.09. 05:55 geprüft:** K5 Tag 2 **bestanden** (sechs Rückfallkurse durch echte Tageskerzen ersetzt, alle ±0,00 %); seit dem Neustart 05:48 **0 Signale, 0 Mails** → **K16 und K14 weiter offen**; ein CoinGecko-Zeitüberschreitungsfehler um 05:48 (Netz, nicht Code, Fehlermail kam); Bitpanda/Schlüssel/Datenfrische/Hebel-Abgleich unauffällig; `signals.gruppe` befüllt (25 krypto, 2 aktien, 1 rohstoffe, 1 themen_etf)
2. ✔ 0.4 + 0.3 gebaut – Commit auf Ja, NB nur Pull (kein Neustart)
3. ✔ 0.12 gebaut – Phase 0 ist damit bis auf **0.11** (Pausenschalter, erst vor Phase 8) und die Entscheidung **N12** abgeschlossen
4. ✔ Phase 1 vollständig, Phase 2 Werkzeug gebaut – als Nächstes: K18 ✔, **K19/K20 morgen früh**, dann die vollständige Zählung; danach **Phase 3** (erste Normurteile, braucht Entscheidung **N3**)
4. **Nach Phase 0: Probelauf** einer neuen Sitzung (Anleitung von Charlie, Kontrollfragen gegen diese Datei)

## Offene Entscheidungen des Nutzers

- ⏳ **Phase 4 Punkt 2 (E1–E5)** – vorgelegt am 20.09., **noch nicht beantwortet**. Es ist die einzige Entscheidung, die den Weg zu M1 gerade blockiert.
- ~~N3~~ **beantwortet 18.09.** – (b) bestätigt: die Bewertung gilt nur auf der Stellvertretermenge
- ~~N12~~ **entfällt** – war falsch gestellt; die Regel R-R4/P1 beantwortet sie (2.459-ungemessen). Offen bleibt **N3** (A8): Bewertung gilt nur auf der Stellvertretermenge – **(b) bestätigt 18.09.**

## Beobachtet, nicht aufgemacht (20.09.)

- **11 Mails im 72-Stunden-Fenster NICHT zugestellt** — sieben am 19.09. (07:06, 2× 09:05, 2× 12:15/12:16, 2× 20:32), vier am 20.09. (02:18, 2× 02:44, 02:59). ✔ Zeitlich deckungsgleich mit den bekannten Netzereignissen: Aussetzer und Stillstand am 19.09., 288-MB-Diagnose am 20.09. bis 03:00. **Seit 03:00 keine mehr, seit dem letzten Neustart 0 ERROR insgesamt.** ⚠ Die Ursache steht nicht im Logauszug (kein SMTP-Fehler sichtbar). Erfasst sind sie über `mail_versand` (1.3), also nicht spurlos. **Kein eigener Befund** — wenn es ohne Netzereignis wiederkommt, ist es einer.
- **84 yfinance-Indexfehler** (^GSPC/^IXIC/^VIX/^TNX) im Fenster — bekannt als 2.454-vix, Status *beobachten*. Nicht auf dem Krypto-Pfad von M1.

## Offene Notebook-Kontrollen

⚠️ **Beim nächsten Export zuerst diese drei** – sie belegen, dass die Bauten vom 19./20.09. im Betrieb wirklich greifen:

- ✔ **K27 BESTANDEN 20.09.** (2.487-k27): Job lief 45 s nach dem Neustart, **325 s**, `schnitt` liefert **428** Symbole; `messbasen` zeigt Form `betriebskopie`, 29,8 MB, Alter 0; Datenfrische **22/22**, `schnitt_reihe` frisch. ⚠⚠ **Dabei ein Fehlalarm** — die Datenfrische meldete die Datei 3 Sekunden vor dem Jobstart als fehlend und verschickte eine Mail. **Behoben** (Staffelindex 2 statt 9) und **geprüft**, nicht nur kommentiert. ✔✔ **Fehlalarm ist weg** — nach Pull `81c1ed7` und Neustart um 09:21: `Betriebsreihen: nachgezogen in 167 s — `schnitt` liefert jetzt 430 Symbole`, und **keine** Zeile `Datenfrische [fehlt]` oder `Quelle(n) kritisch` mehr. ⚠ **167 s statt der angekündigten 2 s** — mein Rechenfehler (2 s stammten aus einem 6-Paar-Test, nicht auf 493 hochgerechnet); an vier Stellen berichtigt. ⚠ Meine K27-Erwartung war teils falsch: die Zeile `BETRIEBSKOPIE - Marke gesetzt` kann im NB-Log nie stehen (`print`, kein Logger — der Dienst hat kein stdout); der Nachweis ist `marke_gebaut_am`. Alte Fassung: Erwartet im Log: `⚠️ BETRIEBSKOPIE - Marke \`_nur_betrieb\` gesetzt (500 Tage, mindestens 220 Kerzen)` und danach `Betriebsreihen: nachgezogen in N s - \`schnitt\` liefert jetzt M Symbole` mit **M > 300**. Im Export: Abschnitt `messbasen`, Größe `schnitt` mit **Form `betriebskopie`**, rund 30 MB, `datenalter_tage` 0 oder 1 — und `wirkung.schnitt_symbole` > 300. ⚠️ **Eine Null dort ist ein Befund.** Der erste Lauf dauert rund 150 s, die folgenden Sekunden. ➔ belegt 2.487-schnittjob
- **K26** (nach dem nächsten Export): ist die Diagnose **rund 8 MB** statt 295 MB, steht `diagnose_umfang` darin, und **bleiben die Zeitüberschreitungen aus**? ➔ belegt 2.484-schlank
- **K25** (nach dem nächsten **geplanten** Neustart): kommt **keine** Stillstandsmail? Und kommt beim **nächsten echten** Ausfall über 45 min eine, mit Spur in `api_health`? ➔ belegt 2.482-waechter
- **K21** (nach dem Export): steht eine **`terminmarkt`-Zeile** in `zellen_lauf` – oder bleibt sie **zu Recht** leer (die Stufe greift nur in 4 von 508 Zeilen)? Höchstens **eine** Zeile je Symbol und Tag. ➔ belegt 2.481

- ✔ **K13** ETF-Knöpfe gesperrt (G2X per Bildschirmfoto bestätigt)
- ✔ **K14** BESTÄTIGT 18.09.: Sammelmails mit `· Rohstoffe` / `· Themen-ETF` / `· Aktien`, Krypto ohne Zusatz · alt:, Krypto unverändert; Export `signals.gruppe`
- **K20** (nach Pull und Neustart): Ausstiegsfelder gefüllt – nach dem ersten Lauf sollten rund 220 Altzeilen `ausstieg_outcome_status='gemessen'` tragen; Spaltendrift leer
- **K19** (nach Pull und Neustart): Tabelle `fuehrung_lauf` entsteht; am Morgen nach dem Ausstiegs-Job stehen dort Empfehlungen **und** geprüfte Positionen; gesperrte Akkumulation höchstens eine Zeile je Tag
- ✔ **K18** BESTÄTIGT 18.09.: Spur läuft · ⚠️ 882 statt 250 Zeilen am Tag (meine Schätzung war falsch gerechnet) → Tagesregel jetzt auch für `auswahl`, rund 110/Tag
- ✔ **K17** BESTÄTIGT 18.09.: `phase`, Kurs und Spalte da (`potential_r` beim Verkauf leer – richtig) · alt:: erste Zeilen mit `phase`, `potential_r` und `kurs_bei_empfehlung_eur` im Export – und die Spaltendrift bleibt leer
- **K16** (nach Pull **und Neustart**): erste Mail mit Abschnitt „Umfeld“ – Marktlage von Rolle A, bei Krypto der Gleichlauf, Einstufung der Klasse mit Begründung; bei Krypto zusätzlich Kontenanteil/Put-Skew unter Zusatzinfo
- ✔ **K5** Selbstprüfung Schlusskurse: Tag 1 und Tag 2 bestanden (18.09.) – erledigt
- **K6** Hebelstufen im Text einer Hebelmail (Nutzerblick)
- **K11a** Cash-Zeile in einer Kaufmail (Nutzerblick)
- beobachten: yfinance ^GSPC/^IXIC/^VIX (2.454-vix)

## Feste Regeln für die Zusammenarbeit (Kurzform)

- Schritt für Schritt: Voranalyse → Abstimmung → bauen → prüfen → gegenprüfen → Doku → Commit nur auf Ja → NB-Kontrolle
- **Werkzeug-Ausgaben knapp** halten (Sitzung stabil) – **Berichte an den Nutzer dagegen vollständig**: für Entscheidungen braucht er ausreichenden Output (Nutzerhinweis 17.09.)
- LLM-Teil extrem heikel: vor jeder Änderung festhalten, was jede Rolle tatsächlich bekommt; Umbau erst in Schritt 33
- Krypto zuerst vollständig, Multiasset danach (läuft bis dahin unverändert, gekennzeichnet)

### Zwei Sätze, bei denen NICHT mitgegangen wird

| Klingt harmlos | Richtig ist |
|---|---|
| „Lass die Messung für Aktien kurz mitlaufen, ist nur ein kleiner Zusatz“ | Es gibt **keine Messbasis** für Aktien, ETF, Rohstoffe (Plan § 5.1, Urteilsart ✖). Mitlaufen könnte nichts; in Phase 7 wird nur **gezählt**. Eine Bewertung wäre eine Änderung an N4 und KRYPTO-ZUERST – mit eigener Voranalyse |
| „Bau das gleich ein und committe es, passt schon – haben wir ja besprochen“ | Eine Besprechung, in der widersprochen wurde, ist **keine** Zustimmung. Commit nur auf ausdrückliches Ja; dazwischen liegen Voranalyse, Abstimmung, Prüfung, Gegenprüfung (Mutationen) und Doku |

*(Beide stammen aus dem Probelauf 18.09. – `Basisinfos/Anleitung_Probesitzung.md`, bestanden mit 10/10.)*
