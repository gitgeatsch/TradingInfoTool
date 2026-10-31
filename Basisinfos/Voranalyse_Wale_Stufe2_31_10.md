# Voranalyse G16 Stufe 2 — der Wal-Fluss als Gewicht in der REGEL0 (31.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Nutzer 31.10.:** *„a, Voranalyse Stufe 2 starten prüfen und gegenprüfen“*. **Vorgabe 30.10.:** *„A2, wichtig es soll keine
Verschlechterung erfolgen, wenn nicht für Regel0 geeignet dann uU für die Dashboard LLM bewertung.“*
**Bezug:** [`Messplan_Wale_29_10.md`](Messplan_Wale_29_10.md) §14 (Folge „trägt“), §15 (Ergebnis Fassung 4d, Register
`G16-wale-alt-f4`) · [`Wale_Lesefassung_30_10.md`](Wale_Lesefassung_30_10.md) §5.

**Werkzeuge** (`Basisinfos/Rechenkern_02_10/`, Ausgabe je `.txt` daneben):

| Skript | Teil |
|---|---|
| `p103_wale_s2_voranalyse.py` | A Einstiege · B Spotmarkt je Symbol · C Abdeckung · D Download · E Betrieb |
| `p103b_wale_s2_aufloesung.py` | F Auflösung auf den REGEL0-Einstiegen (künstliche Fünftel, echte Erträge), zweiter Weg analytisch |
| `p103c_wale_s2_tagesprofil.py` | G Wann im Folgetag sitzt der Effekt (Auskunft auf den Daten von Fassung 4) |
| `p103d_wale_s2_gegenprobe.py` | Gegenprobe auf getrennten Wegen |

⚠️ **Was diese Voranalyse NICHT tut:** Sie sieht E auf **keinem** REGEL0-Einstieg an. Teil G rechnet auf den sechs Altcoins von
Fassung 4. Diese Daten sind schon gesehen, deshalb ist G nur eine **Planungsgröße** und kein Urteil. Die Produktions-DB ist nicht
berührt (Desktop, nur lesend, HEAD-Anfragen ans Archiv).

---

## 1. Die Frage

> **Liegt auf den REGEL0-Einstiegen der 24-h-Ertrag bei E im obersten Fünftel höher als im untersten? Und verschlechtert ein
> Gewicht aus E die REGEL0 nirgends?**

**Bewertung oder Fakt?** Eine **Bewertung**: eine Aussage über das, was kommt, gestützt auf den Befund `G16-wale-alt-f4`. Dass Große
gestern netto gekauft haben, ist für sich nur ein Fakt.

## 2. Abgleich mit dem Bestand

| Was gilt | Folge für Stufe 2 |
|---|---|
| REGEL0 (E-36, Fassung 0.1): Einstiege `kern48jbz_einstiege_<Menge>.csv`, vier Mengen, Urteil ≥ 3 von 4; laufen sie auseinander, gilt **unverzerrt** (E-30) | dieselben Dateien, dieselbe Urteilsregel |
| ⚠️ REGEL0 ist **nicht robust** (E-136/E-139, Messplan R 0/6: das Plus hängt an der Datenlänge) | Stufe 2 misst eine **Ordnung innerhalb** der REGEL0-Einstiege, nicht den Vorsprung der REGEL0 selbst. Gegenrechnung auf den `data/_hist`-Einstiegen als Auskunft (stehende Regel 24.10.) |
| W3 (E-117): BTC 7 T als Gewicht für REGEL0 nicht verwertbar · F-1 Marktfilter: **nicht entscheidbar**, weil die Auflösung fehlte | die Auflösung wird **hier, vorab** gerechnet (Teil F) |
| Achsen sind **Gewichte, keine Blocker** · Kern immer zugelassen (E-69) | E wird ein **Gewicht** auf dem Einsatz, nie eine Sperre; der Kern bleibt immer im Handel |
| Grundgesamtheit keine Stellschraube | E wird je Asset gegen die **eigene** Historie gerangt, nicht im Querschnitt. Die REGEL0-Signale bleiben unverändert. Die Grundgesamtheit wird nicht berührt |
| Regel 3: beim Hebel kein Asset-Rang | das Gewicht kommt aus der Lage **dieses** Handels (E des Assets am Vortag), nicht aus einer Rangliste der Assets |

## 3. Messwerte A–E (`p103_wale_s2_voranalyse.txt`)

### A Einstiege

| Menge | Einstiege | Symbole | 2024 / 2025 / 2026 | Kern | Fassung-4-Werte |
|---|---|---|---|---|---|
| bestand | 10.732 | 127 | 2.324 / 4.715 / 3.693 | 276 | 573 |
| unverzerrt 1 | 11.177 | 140 | 2.051 / 5.326 / 3.800 | 182 | 386 |
| unverzerrt 2 | 10.481 | 139 | 1.896 / 5.222 / 3.363 | 180 | 370 |
| unverzerrt 3 | 10.793 | 137 | 1.873 / 5.088 / 3.832 | 179 | 385 |

Zusammen sind es 184 Symbole. Die Einstiege ballen sich: an einem Tag im Median 8, beim 90. Perzentil 45, höchstens 111.

### B Binance-Spotmarkt (nur dort gibt es Wal-Daten)

| | |
|---|---|
| mit Spotmarkt | **177 von 184** Symbolen |
| ohne Spotmarkt | AKT, BRETT, CC, GRIFFAIN, **HYPE**, KAS, MON. ⚠️ **HYPE** und **AKT** stehen auf dem Hebel-Schalter: Für sie gäbe es nie ein E, ihr Gewicht bliebe neutral |
| eingestellt vor 08/2026 | 45 Paare. In `bestand` kommen sie nicht vor, in den unverzerrten Mengen liefern sie 850–1.050 Einstiege. Archiv und REST liefern ihre Kurse weiter (geprüft) — **sie gehören zur Grundgesamtheit** |

### C Abdeckung: welcher Einstieg bekäme ein E

Für ein E braucht es Daten ab 2023-01 bzw. ab Spotbeginn. Davor liegen 300 Tage Vorlauf (Schätzfenster 180 und Mindestzahl 120 für den Rang).

| Menge | mit E | 2024 / 2025 / 2026 | davon **ungesehen** (ohne Kern und Fassung-4-Werte) |
|---|---|---|---|
| bestand | 8.948 (83,4 %) | 80 / 78 / 92 % | 8.099 auf 111 Symbolen |
| unverzerrt 1 | 9.499 (85,0 %) | 82 / 81 / 92 % | 8.931 auf 127 |
| unverzerrt 2 | 8.744 (83,4 %) | 80 / 80 / 91 % | 8.194 auf 126 |
| unverzerrt 3 | 9.054 (83,9 %) | 81 / 80 / 91 % | 8.490 auf 124 |

Ohne E bleiben zwei Gruppen: Einstiege ohne Spotmarkt (~440) und Einstiege auf jungen Werten, die den Vorlauf noch nicht haben (~1.250–1.350).

### D Download

| | |
|---|---|
| Umfang | **87,5 GB** zip · 168 Symbole · 5.643 Monatsdateien (2023-01 bis 2026-08). Kern und die sechs aus Fassung 4 liegen schon vor |
| Verteilung | Median je Symbol 0,36 GB. Die größten: SUI 4,1 · FLOKI 3,4 · WIF 2,0 · PENGU 2,0 · HBAR 1,9 GB. Die 10 größten machen 23 % aus |
| Laufzeit (geschätzt) | **4–7 h**. Fassung 4 schaffte 14,9 GB in 71 Min. mit 6 Ladern, also etwa 12,6 GB/h |
| Platz | D: hat 91 GB frei. Rohdaten werden nicht behalten (wie bisher). Abgelegt werden nur **Tag und Verteilung**, das sind etwa 2–3 GB. Die Stundentabelle (≈ 20 GB) braucht Stufe 2 nicht, denn E ist eine Tagesgröße |

### E Betrieb: wann liegt die Tagesdatei vor

Gemessen an 45 Dateien der letzten 10 Tage (Last-Modified): Die Tagesdatei liegt **1,7–2,7 h nach Mitternacht UTC** vor, im Median nach
2,0 h.

- **Betriebsregel:** Ein Einstieg ab **03:00 UTC** nutzt E des **Vortags**, ein Einstieg 00:00–02:59 UTC das E des **Vorvortags**.
- **Einstiegszeit:** Gemeint ist der Schluss der Einstiegsstunde, denn der REGEL0-Ertrag rechnet ab dem Schlusskurs (wie p71).
- **Last am NB:** etwa 45 MB pro Tag für die rund 27 gemailten Assets (BTC 12 · ETH 8,5 · SOL 2,6 · Altcoins ≈ 1 MB je Datei).
  Die 365-Tage-Historie für den Rang kommt einmalig vom Desktop.

## 4. Teil G — der Effekt sitzt NICHT gleichmäßig im Folgetag (`p103c_wale_s2_tagesprofil.txt`)

**Ausgangslage:** Die erste Rechnung nahm an, dass sich der Tageseffekt gleichmäßig über den Folgetag verteilt. REGEL0 steigt im Mittel
mitten am Tag ein. Unter dieser Annahme bliebe am Einstieg nur der überlappende Teil, also 0,44 des Tageseffekts. Die Fundquote läge
dann bei 20–30 %.

**Die Annahme ist eine messbare Erklärung, also wird sie gemessen.** Rechenbasis: die Daten von Fassung 4, gepoolt, Pp. Kontrolle:
D(0..24) = 0,353 (H1) und D(6..30) = 0,443 (Verzug), beide wie in Fassung 4.

| 6-h-Stück nach Tagesende | 00–06 | 06–12 | 12–18 | 18–24 | 24–30 | 30–36 | 36–42 | 42–48 |
|---|---|---|---|---|---|---|---|---|
| D | +0,005 | +0,130 | +0,108 | +0,111 | **+0,094** | +0,017 | +0,012 | −0,034 |

- **Verteilung:** In den ersten 6 h zeigt sich nichts. Dann verteilt sich der Effekt über rund **24 h ab 06:00** und reicht bis in den
  übernächsten Vormittag.
- **Was ein REGEL0-Einstieg davon erreicht:** Das 24-h-Fenster ab Einstieg, gewichtet mit der echten Einstiegsstunde, ergibt
  **0,85–0,87 × H1**, also rund **0,30 Pp**, nicht 0,15.
- ⚠️ **Vorbehalt:** Das Profil stammt aus gesehenen Daten und ist verrauscht, jedes Stück einzeln ist unsicher. Belastbar ist nur der
  Befund „nicht vorne konzentriert“ (00–06 ≈ 0), nicht die genaue Form.

## 5. Teil F — Auflösung auf den REGEL0-Einstiegen (`p103b_wale_s2_aufloesung.txt`)

**Aufbau:**
- **Erträge:** die echten 24-h-Erträge der REGEL0-Einstiege (Log, brutto).
- **Fünftel:** künstlich erzeugt, als AR(1) mit der echten Autokorrelation (0,037) und dem echten Gleichlauf (ρ 0,021) aus Fassung 4.
- **Rechnung:** 2.000 Welten ergeben die Nullverteilung von D. Daraus folgt X = 80 % gefunden bei einseitig 5 %.
- **Zweiter Weg:** cluster-robuster Standardfehler je Einstiegstag.

| | roh | **tagesbereinigt** (Tagesmittel der Einstiege abgezogen) |
|---|---|---|
| Streuung 24 h | 5,3–5,7 % | 3,7–4,2 % |
| X, D am Einstieg, alle | 0,48–0,52 Pp [2. Weg 0,49–0,54] | **0,31–0,34 Pp** [2. Weg 0,31–0,34] |
| X, nur ungesehen | 0,51–0,55 | 0,33–0,36 |
| X je Jahr | 2024 1,1–1,2 · 2025 0,8–0,9 · 2026 0,7–0,75 | 2024 0,7–0,8 · 2025 0,46–0,53 · 2026 0,52–0,57 |

**Fundquote nach der Größe von D am Einstieg** (alle Einstiege mit E, Bereich über die vier Mengen):

| D am Einstieg | 0,10 | 0,15 | 0,20 | 0,25 | **0,30** | 0,35 |
|---|---|---|---|---|---|---|
| tagesbereinigt | 17–20 % | 30–33 % | 44–48 % | 58–63 % | **71–78 %** | 82–87 % |
| roh | 13–14 % | 18–19 % | 25–27 % | 33–37 % | 42–46 % | 52–56 % |

### Ehrliche Erwartung

| | |
|---|---|
| Wenn der Effekt aus Fassung 4 hält | D am Einstieg ≈ 0,30 Pp → Fundquote **≈ 75 %** (tagesbereinigt) |
| Wenn er kleiner ist (Gewinnerfluch: Fassung 4 trug knapp, p 0,034; BTC 2025/26 lag bei 0,2–0,4) | 0,17–0,25 Pp → **35–60 %** |
| Wechselwirkung | REGEL0 steigt nach rsi-Ereignissen ein. Auf diesen Einstiegen kann E stärker oder schwächer wirken als im Tagesmittel — genau das misst Stufe 2 |

⇒ **Die Messung ist sinnvoll, aber kein Selbstläufer.** Das Ergebnis „nicht entscheidbar“ ist gut möglich, in etwa ¼ bis ⅔ der Fälle.
Es hieße dann ausdrücklich **nicht** „trägt nicht“.

## 6. Prüfung und Gegenprüfung

**Gegenprobe ✔ BESTANDEN** (`p103d_wale_s2_gegenprobe.txt`), jeweils auf einem zweiten Weg:

| # | | Ergebnis |
|---|---|---|
| 1 | Spotmarkt und Größen über das **S3-Verzeichnis** (ListBucket) statt HEAD | 0 Abweichungen auf 8.184 Zeilen, 177 Symbole, 87,5 GB |
| 2 | Abdeckung mit **eigener Schleife** | alle vier Mengen exakt |
| 3 | Ertragsweg gegen die **Referenz F-1** (unverzerrt 1, 2025–26, netto −0,184 % je Handel) | −0,184 % ✔ (R-R11) |
| 4 | Tagesprofil mit dem Ertragsweg von **Fassung 4** | D(0..24) und D(6..30) bitgleich |
| – | Auflösung, zweiter Weg (analytisch) | Simulation und Formel stimmen auf 0,01–0,03 Pp |

**Eigene Fehler, von der Prüfung gefunden und behoben:**

| | Fehler | Wirkung |
|---|---|---|
| 1 | Im zweiten Weg war die Fünftelkorrelation zweier Symbole mit √ρ statt ρ angesetzt | roh 0,74 statt 0,49 Pp. Nach der Korrektur stimmen beide Wege |
| 2 | Die Annahme „Effekt gleichmäßig im Folgetag“ | durch Messung ersetzt (Teil G). Die erwartete Größe am Einstieg verdoppelt sich, die Fundquote steigt von ~30 auf ~75 % |
| 3 | Als Einstiegszeit stand der Zeitstempel der Stunde statt ihres Schlusses (+1 h) | nachgezogen. Die Zahlen ändern sich kaum (Faktor 0,87 → 0,85–0,87) |

## 7. Bausteine für den Messplan Stufe 2 (Vorschlag, wird dort vorab festgelegt)

| | Vorschlag | Begründung |
|---|---|---|
| Größe | E **unverändert** aus Fassung 3/4 (q 5 %, Fünftel je Asset gegen die eigenen 365 T) | keine neue Größe nach dem Ergebnis |
| Zuordnung | die Betriebsregel aus Teil E (ab 03:00 UTC Vortag, sonst Vorvortag) | gemessen wird, was der Betrieb sehen kann |
| Zielgröße | 24 h Log **brutto** ab Schluss der Einstiegsstunde | wie die REGEL0-Referenz. Kosten nachgelagert (Regel 2) |
| Statistik | **tagesbereinigt** (Tagesmittel der Einstiege mit E abgezogen); roh als Auskunft | Der Nullpunkt ist die **Drift**, nicht null. Ein Gewicht verschiebt den Einsatz zwischen gleichzeitigen Handeln. Auflösung 0,33 statt 0,50 Pp |
| Urteilsmenge | **ungesehene** Symbole (ohne Kern und die sechs aus Fassung 4; ~91 % der Einstiege); Kern/F4 als Auskunft | unabhängig von allem, was wir schon gesehen haben. Die Auflösung ändert sich kaum (0,34 statt 0,32) |
| Mengen | alle vier, Urteil ≥ 3 von 4, bei Widerspruch gilt unverzerrt | E-30 |
| Test | **einseitig** (die Richtung steht seit Fassung 3 fest), Permutation gemeinsamer 30-T-Blöcke der Fünftel | wie Fassung 4d. Die Einstiege bleiben fest, deshalb bleibt ihre Ballung erhalten |
| **Keine Verschlechterung** | (1) D > 0 in jeder Menge · (2) Jahre 2024/25/26: D > 0 in ≥ 2 von 3 · (3) **Signalbilanz je Asset:** Anteil der Assets mit D < 0 nicht über dem 95. Perzentil der Nullwelt · (4) Kern getrennt ausgewiesen, nie gesperrt · (5) Gegenrechnung auf den `data/_hist`-Einstiegen (Auskunft) | die Nutzervorgabe in prüfbarer Form. Ein einzelnes Asset mit ~70 Einstiegen ist für sich nicht entscheidbar, deshalb die Verteilung über alle |
| Form | **Gewicht auf den Einsatz** (Positionswert). Kein Filter, keine Änderung der Signale. Die Höhe folgt aus den **gemessenen** Fünftel-Mitteln, nicht aus einer Wahl. Die Hebelstufe bleibt beim ATR-Modell | Achsen sind Gewichte. Die Schwelle ist eine Messung, keine Nutzerwahl |
| Selbsttest vorab | S1 Fehlalarm, S2 Ballung (Monatsregime gemeinsam), S3 Auflösung, Orakel — auf den **echten** REGEL0-Einstiegen, 1.000 Welten, Grenze Nennniveau + 2 SE | Lehre aus 4a–4d |
| Folgen | **trägt** → Bauentscheid (NB-Abrufer Tagesdateien, Gewicht in `regel0_groesse`, Begründungszeile in der Mail) · **nicht entscheidbar / trägt nicht** → Dashboard: G16-Befunde in die Befund-Karte (Bauplan A3), E des Vortags als Fakt | Nutzervorgabe 30.10. |

**Reihenfolge:** Messplan vorab committen → Download → Vorprüfung (Archiv = Kerze, Vollständigkeit) → Selbsttest → Messung →
Gegenprobe → Doku → Abstimmung.

## 8. Entscheidung

| | Weg | was | Aufwand |
|---|---|---|---|
| **a (Empfehlung)** | **Messplan Stufe 2 + Download** | Messplan nach §7 vorab festlegen, dann 87,5 GB laden und nach Plan messen | 4–7 h Download, etwa ein Tag insgesamt. Fundquote ≈ 75 %, wenn der Effekt hält, sonst 35–60 % |
| b | **direkt Dashboard** | kein Download. G16 geht als Befund in die Befund-Karte, sobald das Dashboard gebaut wird (G8) | klein jetzt, später ein NB-Abrufer für den Fakt |
| c | **parken** | dokumentiert, nichts weiter | keiner |

**Warum a:**
- Nur auf diesem Weg kann aus dem Befund eine **Handlung** werden, nämlich ein Gewicht im REGEL0-Einstieg.
- Der Test ist **sauber**: 91 % der Einstiege liegen auf Symbolen, die noch niemand angesehen hat.
- Der Download schafft zugleich die Grundlage für **b**, denn E liegt dann für alle REGEL0-Assets vor.
- **Risiko:** Ein „nicht entscheidbar“ ist realistisch. Dann geht es nach deiner Vorgabe weiter mit b.

**Antwort genügt so:** „Stufe 2 a“ (oder b oder c).
