# Voranalyse L2 · N3 — Überschneidung der tragenden Beiträge (30.09.2026)

**Auftrag (Nutzer 30.09.):** *„ja, N3 Voranalyse schreiben — prüfen und gegenprüfen"*
**Vorher:** Befund **2.691** (L2-Bestätigung), `Voranalyse_L2_Kern_anheben_30_09.md` Abschnitte 14–15.

---

## 1. Worum es geht — und was es fürs Ziel bringt

Auf den Kern-Einstiegen heben **zwei** Beiträge das **Potential** (wie weit der Kurs in 24 h läuft), beide ATR-frei geprüft (2.691):

| Beitrag | was er misst | Potential oben gegen unten (2025–26) |
|---|---|---|
| `ema_abstand_atr` oben | der Kurs steht **über** seinem 48-h-EMA, in eigener ATR (oberes Drittel: mehr als 0,43 ATR) — *er ist schon in Fahrt* | +0,14..+0,16 ATR (4/4) |
| `volumenschub` oben | das Stundenvolumen liegt **über** dem Mittel der eigenen letzten 24 h (oberes Drittel: mehr als 1,14-fach) — *es kommt Geld rein* | +0,08..+0,10 ATR (3/4) |
| dazu: **Ruhe 48 h** | vor dem Überschreiten 48 h **unter** der Schwelle — *aus dem Stand* | +0,014..+0,032 ATR (3/4) |

**Die Frage:** Sind das **drei Informationen** oder im Kern **eine** (*Anfahren mit Wucht*)? Wer in Fahrt ist, hat oft auch
Volumen — und nach langer Ruhe sind beide vielleicht häufiger.

**Warum das entscheidet (Ziel *optimale Lage*):**
- Die **Summe** (L4) darf jede Information nur **einmal** zählen. Zählt sie dieselbe doppelt, wirkt die Summe stärker, als
  sie ist — der Einstieg würde zu optimistisch bewertet.
- Tragen sie **getrennt**, addiert sich das Potential: die Einstiege, an denen **beides** zutrifft, sind die *optimale Lage*
  des Kerns — genau das, was du suchst (*hohe Anstiege erfassen*).
- ⚠️ Es ist eine **Messung ohne neue Daten** — die Einstiege, Kanten und Richtungen liegen seit der Wahl fest.

---

## 2. Prüfen, was schon da ist (Pflicht: bestehendes Schema zuerst)

| | Stand | Folge für N3 |
|---|---|---|
| Rollen (25.09./29.09.) | beide sind **Rolle B** (*wie weit*), ema_abstand am **unteren** Ende auch Rolle C (Risikosperre, 2.642) | N3 misst die Rolle B; das Risiko von ema oben (etwas mehr Rückgang, 2.691) läuft als Auskunft mit |
| 2.667 | volumenschub trägt **über die ATR hinaus** (30 von 32 Monaten) | passt zu G-ATR |
| 2.681 | als **Risiko**kurve der Hebelstufe bringen beide nichts über die ATR | N3 prüft **nicht** das Risiko — Bewertung 2 bleibt die ATR |
| 2.691 | Richtung **oben** für beide, Kanten aus 2024 in `data/_vergleich/l2_wahl_bestand.json` | **fest übernommen**, nichts neu gewählt |
| Überschneidung schon gemessen? | nein — in keinem Befund; die Wahl §12 Punkt 4 hat sie ausdrücklich hierher verschoben | echte offene Frage |

---

## 3. Die Messung — vorab festgelegt

**Menge:** die Kern-Ersteintritte (s = +0,035, wie 2.688/2.691). **Maß (Urteil): Potential** (MFE 24 h in eigener ATR minus
eigenes Normal). Chance und Risiko laufen als Auskunft mit. **Kanten und Richtungen** aus der Wahl 2024 (JSON), unverändert.

| # | was | Art |
|---|---|---|
| **N3-1** | Spearman-ρ(ema_abstand, volumenschub) und die **3×3-Tafel** (Drittel × Drittel): Zahl, Chance, Potential, Risiko je Zelle | Auskunft |
| **N3-2** ⭐ | **Eigenanteil**: der Effekt von X (oberes minus unteres Drittel) **innerhalb** jedes Drittels von Y, gemittelt (jede Zelle ≥ 30 Einstiege) — für X = ema gegeben volumenschub **und** X = volumenschub gegeben ema | **Urteil** |
| **N3-3** | **Ruhe gegen Wucht**: 48 h minus 24 h Ruhe, **innerhalb** der ema-Drittel und **innerhalb** der volumenschub-Drittel; umgekehrt N3-2 auf den 48-h-Einstiegen | Urteil (Ruhe) + Auskunft |
| **N3-4** | **Zusammentreffen**: Potential der Zelle *beide oben* gegen *nur ema oben* und gegen *nur volumenschub oben* | Auskunft |

**Regel „eigene Information"** (je Beitrag): der Eigenanteil ist **> 0** und **≥ 50 % seines Roheffekts** in derselben Menge.
(Dieselbe Schwelle wie G-ATR — keine neue Zahl.)

**Ablauf wie immer — erst Wahl, dann einmal Bestätigung:**

| Schritt | Menge | was entschieden wird |
|---|---|---|
| **Wahl 2024** (bestand) | nur 2024 | die **Form** per Regel: beide eigen → **zwei Glieder**; nur einer eigen → der andere steckt in ihm → **ein Glied** (der eigene); keiner eigen → **eine** Information → der mit dem größeren Roheffekt |
| **Bestätigung** einmal 2025-01..2026-08 | 4 Mengen | die gewählte Form: Eigenanteil **> Null-P90** (Beitrag je Asset verschoben, 40 Ziehungen, Bestes-von-k), **> 0 in 2025 und 2026**, **Tagesblock** untere Grenze > 0, **≥ 3 von 4 Mengen** |
| Ruhe (N3-3) | beide | Ruhe **eigen**, wenn 48 − 24 h innerhalb **beider** Schichtungen > 0 und ≥ 50 % des Roheffekts, 2025 und 2026, ≥ 3/4 Mengen |

⚠️ **Ehrlich zur Datenlage:** 2025–26 ist für die **einzelnen** Beiträge schon einmal gesehen (2.691), für ihr
**Zusammenspiel** nicht. Die Form wird deshalb **nur auf 2024** gewählt; der wirklich ungesehene Prüfstein sind die Monate
**ab 2026-09**, sobald sie in der Messbasis sind (Optimierungsloop).

---

## 4. Prüfung und Gegenprüfung

| Prüfung | wie |
|---|---|
| **R-R11** | Kern-Einstiege 2.095 (2024) / 10.534 (bestand 2025–26); Roheffekte ema +0,174 (2024) / +0,1619 (2025–26), volumenschub +0,129 / +0,0953 **bitgleich** zu §12 und 2.691 |
| **Nullwelt** | Eigenanteil gegen den **je Asset verschobenen** Beitrag, 40 Ziehungen, Bestes-von-k über die getesteten Eigenanteile |
| **Zeitstabilität** | 2025 und 2026 getrennt |
| **Weglassprobe** | jeder Beitrag einmal **ohne** den anderen (Roheffekt) und **mit** ihm (Eigenanteil) — das ist die Frage selbst |
| **Mehrfachtesten** | 2 Eigenanteile (+2 für die Ruhe), Bestes-von-k |
| **Je Asset** | Anteil der Assets mit positivem Eigenanteil (Auskunft; ≥ 10 je Zelle) |
| **Auswahlanteil** (Gegenprüfung) | die Zelle *beide oben* ist klein — Vergleich mit zufällig auf dieselbe Zahl **ausgedünnten** *ema oben* (40 Ziehungen, P90); sonst misst N3-4 nur die Härte |
| **Prozentmaß** | alles zusätzlich in Prozent (Auskunft, wie G-ATR) |

---

## 5. Umfang

Eine Wahl (bestand, 2024) und vier Bestätigungsläufe — je Lauf etwa **3–8 Minuten**, keine lange Messung, **keine Stufe 1
nötig**. Ablauf: Werkzeug `messe_losfahren.py --l2 --n3` bauen → Funktionstest → **committen** → Wahl → **Stopp und Bericht**
→ nach deinem Ja die Bestätigung.

---

## 6. Zur Abstimmung (P1–P5)

| # | Vorschlag |
|---|---|
| **P1** | N3-1 bis N3-4 wie oben, **Potential** als Urteilsmaß, Kanten und Richtungen aus der Wahl 2024 unverändert |
| **P2** | Regel *eigene Information* = Eigenanteil > 0 und ≥ 50 % des Roheffekts (wie G-ATR) |
| **P3** | Wahl der **Form** nur auf 2024, Bestätigung einmal auf 2025–26 in 4 Mengen, ≥ 3/4 |
| **P4** | die **Ruhe 48 h** in dieselbe Prüfung (N3-3) — ist sie eigen oder nur ein anderer Weg zur Wucht? |
| **P5** | Ergebnis → die **Summe (L4)** mit genau den Gliedern, die eigen sind; dann N4 Simulation als Erfolgsmessung |

---

## 7. Im Plan vorgesehen — die Hypothesenfrage *„der Kern ist ein Schalter"* (Nutzerhinweis 30.09.)

**Nutzer:** *„dass der Kern wie ein Schalter funktioniert, war nicht Absicht — wenn es fachlich nicht anders möglich ist, ok.
ABER dadurch gibt es Vor- und Nachteile zu bewerten. Nach der Phase Kern heben noch einmal zur Hypothesenfrage gegenprüfen."*

**Was gemessen ist — und was nicht:** A1 hat die Stärke **in der Stunde des ersten Überschreitens** gemessen. Dort liegen
**80 % der Einstiege zwischen +0,035 und +0,044** (Klassengrenzen der Wahl: 0,0368 / 0,0383 / 0,0396 / 0,0443). Die Stärke
**kann** in dieser Stunde kaum streuen — der Schalter ist damit zu einem guten Teil **Folge der Einstiegsform**, nicht
zwingend eine Eigenschaft des Marktes. **Nicht** gemessen ist, ob ein **stärkerer Zustand** (rsi länger oder deutlicher oben)
mehr bringt — der Zustand war als Zahl nicht kalibriert (2.687), das ist aber eine andere Frage.

| | Schalter (heute) | abgestufte Bewertung |
|---|---|---|
| **Vorteile** | klarer **Zeitpunkt** (der Übertritt); wenige Parameter, kaum Überanpassung; gleich für jedes Asset (neutral); die Abstufung kommt aus der **Summe** der anderen Beiträge — so ist das Beitragssystem gedacht | eine Zahl je Einstieg: Rangfolge gleichzeitiger Signale, **Dosis-Wirkung** für Größe und Mail |
| **Nachteile** | alle Kern-Signale sind **gleich viel wert**; rsi liefert keine Dosis — die Abstufung muss **vollständig** aus den anderen Gliedern kommen; der Zustand *rsi schon hoch* (späte, große Bewegungen) fällt durch die Form heraus | braucht eine Größe, die **streut und kalibriert** ist — der Zustand war es nicht (2.687) |

**Meine Einschätzung:** Für den **Einstieg** ist der Schalter fachlich richtig — ein Übertritt ist ein Ereignis, kein Grad.
Die Abstufung, die du für *optimale Lage* brauchst, sollte aus der **Summe** kommen (Kern + Ruhe + Wucht). Genau das ist die
Hypothese, die **nach Kern heben** (nach L4) zu prüfen ist:

| **H-Schalter** (im Plan, nach L4) | vorab festzulegen, wenn es so weit ist |
|---|---|
| Hypothese | die **Summe** ordnet monoton (je höher, desto mehr Potential und Chance) — die Abstufung, die rsi allein nicht hat |
| Gegenhypothese | eine andere **Stärkeform** des rsi ordnet doch: Anstieg des Vorsprungs über die letzten Stunden, Abstand über der Schwelle nach 1–3 h (Positionsführung), Zustandsdauer |
| Bewertung | Vor- und Nachteile oben gegen das Ergebnis halten; entscheiden, ob der Kern Schalter bleibt |
