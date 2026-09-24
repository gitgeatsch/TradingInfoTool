# Alle offenen Punkte — Hebel, Stand 24.09.2026

**Nutzerauftrag:** *„Nein zuerst müssen wir alle Fakten am tisch haben bevor
wir vom Ziel abweichen, zuerst alle offenen Punkte klären."*

⚠️ **Kein Punkt wird hier entschieden.** Dieses Blatt sammelt, was offen ist,
sagt bei jedem **woran es hängt**, **was es kostet** und **ob es den Hebel
blockiert**. Entscheidungen danach.

---

# § 0 ⭐ Die fachliche Vorklärung, die vieles vereinfacht

> **Spot und Hebel sind nicht zwei Geschäfte, die man vergleichen muss —
> sie sind dasselbe Geschäft in zwei Größen.**

Gleicher Einstieg, gleicher Stop, gleiches Ziel, gleiche Richtung.

| | |
|---|---|
| **In R gemessen sind sie IDENTISCH** | R *ist* der Verlust am Stop. Der Hebel skaliert Gewinn und Verlust gleich — **gemessen** (2d, 24.09.) |
| ➤ **Folge** | eine Bewertung in R kann die beiden **grundsätzlich nicht** unterscheiden. Das ist keine Messschwäche |

**Was sie trennt, ist die GEOMETRIE:**

| | Spot | Hebel |
|---|---|---|
| Erwartungswert in R | identisch | identisch **− Finanzierung** |
| Kapitalbindung | hoch | niedrig |
| laufende Kosten | keine | **0,18 %/Tag** (2d gemessen) |
| Risiko | max. Einsatz | **mehr als der Einsatz** |

➤ **Hebel gewinnt bei kurzem Trade und engem Stop. Spot bei langem Trade
oder weitem Stop.**

⚠️⚠️ **KORREKTUR 24.09., am Code gegengeprüft.** Die erste Fassung nannte
hier `hebel_noetig = verlustanteil / stop_rel`. **Das ist der ALTE
Risikobudget-Weg** (`dimensioniere()`, Zeile 1693) und **nicht** der aktive.

**Aktiv ist `hebel_aus_quote` — und der Hebel kommt aus der BEWERTUNG:**

```yaml
hebel_aus_quote:
  aktiv: true        # risiko = r(q) x Kapital,  r(q) = halbes Kelly
  hebel_ab: 2.0      # hebel = (risiko / Stop) / 500
  hebel_grenze: 5.0  # unter hebel_ab wird es Spot
```

`entscheidungsrechnung.py:1033` — `hebel_noetig = risiko_eur / (betrag ×
stop_rel)`, und `risiko_eur` stammt aus **`r(q)`**.

✔✔ **Damit ist die Nutzervorgabe *„der HEBEL MUSS dynamisch aus der Bewertung
entstehen"* bereits erfüllt** — und auch die Auswahl „spot oder hebel" hängt
an ihr: `hebel_ab: 2.0` ist die Schwelle.

⛔ **ABER auf einer unkalibrierten Grundlage** — siehe **P-9** und **P-22**.

⛔ **Eine Regel „Hebel schlägt Spot" wäre falsch** — eine Vorrangregel ohne
Messung, und damit ein Verstoß gegen Regel 3.

⚠️⚠️ **DIE ECHTE LÜCKE IST EIN FAKTOR, KEINE BEWERTUNG: die HALTEDAUER.**
0,18 %/Tag sind bei 6 h **0,045 %** und bei 20 Tagen **3,6 %**. Sie geht in
die Entscheidung heute **nicht** ein. → **P-11**

---

# § 1 Was BLOCKIERT — ohne diese kein Hebelsignal

| # | Punkt | hängt an | Lage |
|---|---|---|---|
| **P-1** | ⭐ **Die Auswahlstufe rangt nach 250 Handelstagen** und sperrt im Hebel-Lauf **6 von 6** weg | Messfrage: welches Rangfenster trägt für 6–72 h? | ✔ **Nutzerentscheidung 24.09.: als Messfrage aufsetzen** |
| **P-2** | **Die Kette läuft vor der Bewertung** — Modellurteil ist Stufe 8, Bewertung Stufe 12 | Nutzervorgabe 24.09.: *„die Kette erst nach einer erfolgreichen Bewertung durchlaufen"* | ⛔ **Reihenfolgeumkehr, nicht gebaut** |
| **P-3** | **Trichterstufe 6 sperrt `oi_fuenftel >= 4` hart** — genau die Hebel-Lage | offene Messfrage *„sperren oder bewerten"*; betrifft **auch** `spot × einstieg` (M1-Kriterium 1, das durch ist) | ⛔ **Nutzerentscheidung nötig** |

⚠️ **P-3 ist der Grund, warum B0 den Bewertungsumbau kippte:** alle vier
Kandidaten tragen **nur** auf dem Fünftel, das die Kette nie sieht.

---

# § 2 Was ENTSCHIEDEN werden muss — Geld und Risiko

| # | Punkt | Lage |
|---|---|---|
| **P-4** | ⚠️⚠️ **Der Risikodeckel sieht nicht alles.** Ein Hebel-Signal mit `max_safe_hebel → 1,0` (KAITO 9,9 %, CAT 17,4 % Stop) bekommt das Etikett `spot`, fällt aus dem **3.000-EUR-Hebel-Topf** und dem Hebel-Cooldown — trägt aber den Betreff „EROEFFNEN (Hebel)" | ⛔ **offen** |
| **P-5** | **Die Beträge.** Vor S6b 800 € (spot) / 1.000 € (hebel); heute eine Zahl je Gruppe × Strategie | ⛔ **Geldentscheidung, offen** |

⚠️ **P-4 ist unabhängig von der Bauform** — er trifft jede Lösung, in der ein
Hebel-Einstieg entstehen kann.

---

# § 3 Was GEMESSEN werden muss

| # | Punkt | Datenlage | Lage |
|---|---|---|---|
| **P-6** | **Vorabfestlegung 10 — die sechs Kandidaten auf der Stundenbasis** | ✔ **liegt jetzt vor**: 3.244.186 Kerzen, 116 Symbole, 2021-12 bis heute | ⚠️ **bereit, ungemessen** |
| **P-7** | **Das Rangfenster für 6–72 h** (= P-1) | dieselbe Basis | ⚠️ Vorabfestlegung fehlt |
| **P-8** | ⭐ **Der AUSSTIEG als eigene Stellgröße.** Gemessen 24.09.: bei 72 h standen **21,1 %** der Trades über +1 R und schlossen darunter | ✔ Stundenbasis | ⚠️ **erkannt, nicht angefasst** |
| **P-9** | **`q` wurde nie kalibriert** — steuerndes Fenster 1 Pp, funding bewegt 3; in 44 % der Merkmalslagen gibt es gar keinen Hebel | — | ⛔ **alt, ungelöst** |
| **P-10** | **Der Hebel ist zu GROB**, nicht zu schwach — Stufen 1,47× / 1,85× zu groß (N19, 06.09.) | — | ⛔ **alt, ungelöst** |
| **P-11** | ⭐ **Die HALTEDAUER geht in die Spot/Hebel-Entscheidung nicht ein** (§ 0) | 0,18 %/Tag ist gemessen (2d) | ⚠️ **neu erkannt 24.09.** |
| **P-22** | ⭐⭐ **Die BEWERTUNGSSTUFEN** — welches Bewertungsniveau rechtfertigt welche Hebelstufe? Nutzerauftrag 24.09. | ⚠️ **N19-E ist eine Entscheidung vom 06.09., die nie gebaut wurde** — es fehlt keine Messung, sondern die Umsetzung | ⛔ **nach P-1, und nach P-9** |

---

# § 4 Was NACHGEZOGEN werden muss — Technik

| # | Punkt | Lage |
|---|---|---|
| **P-12** | **6 Suite-Prüfungen** schreiben den S6b-Zustand fest und werden bei jeder Bauform rot, die den Hebel zurückbringt | ⚠️ **Prüfungen müssen beide Welten setzen**, nicht eine annehmen |
| **P-13** | **`hebel_signals` hat seit dem 10.08. keinen Schreiber** (`hebel_analyst` ohne Aufrufer, 2.343) — `positionsfuehrung` liest die Tabelle bereits | ⚠️ zu klären, wohin ein Hebelsignal geschrieben wird |
| **P-14** | **Der Docstring von `assetklassen.zellen()` sagt „NOCH OHNE AUFRUFER"** — `rollen_lauf:732` ruft es seit Wochen | ⚠️ **falsche Doku**, führt jeden Leser in die Irre |
| **P-15** | **`messnorm_auswahl.py:23`** trägt einen veralteten Docstring (*„die Barriere hat hier nichts zu suchen"*) | ⚠️ klein |

---

# § 5 Der LLM-Teil — vollständig offen

| # | Punkt | Lage |
|---|---|---|
| **P-16** | **Die LLM-Rollen kennen die Bewertung mit keinem Wort** (2.398) — sie liefern **vor** Stufe 12 | ⛔ Block **L-ROLLEN**, Reihenfolge *D vor L* |
| **P-17** | **Weiß das Modell, dass es ein Hebelgeschäft ist?** Der Prompt ist für `spot`/`hebel` **bitgleich** | ⛔ offen |
| **P-18** | **Darf das LLM etwas verwerfen?** Steht seit Wochen im Plan | ⛔ offen — stehende Vorgabe: *LLM ist Prüfung, nicht Entscheider* |

⚠️ **P-2 verschärft P-16/P-17:** kommt die Bewertung vor das Modell, ändert
sich, **was** das Modell überhaupt zu sehen bekommt.

---

# § 6 Nebenthemen — eingeordnet, nicht vergessen

| # | Punkt | Lage |
|---|---|---|
| **P-19** | **Takt und Cooldown** — Nutzerhinweis 24.09.: *„der cooldown ist ohnehin eine künstliche Grenze und sollte verringert werden wenn das system funktioniert"* | ⚠️ **nach der Ablaufkette einordnen** |
| **P-20** | **Der Stop kommt aus dem TAGES-ATR** — für einen 6-h-Trade zu weit. Gemessen: mit `× √(H/24)` wird die Ausgangsverteilung haltedauerneutral | ⚠️ **gemessen, nicht gebaut** |
| **P-21** | **1 Symbol fehlt in der Stundenbasis** (GAS, Netzabbruch) | ✔ trivial — Wiederaufnahme ist eingebaut |

---

# § 7 ⚠️ Die ehrliche Gesamtlage

| | |
|---|---|
| **Blockierend** | **3** (P-1, P-2, P-3) |
| **Entscheidung nötig** | **2** (P-4, P-5) |
| **Messbar, Daten liegen vor** | **3** (P-6, P-7, P-8) |
| **Neu 24.09.** | **1** (P-22 Bewertungsstufen) |
| **Alt und ungelöst** | **2** (P-9, P-10) |
| **Technik nachziehen** | **4** (P-12 bis P-15) |
| **LLM** | **3** (P-16, P-17, P-18) |

⚠️⚠️ **Der kürzeste Weg zu einem echten Hebelsignal führt über P-1, P-2 und
P-4** — und **keiner** davon braucht eine eigene Hebelbewertung. Das ist die
gute Nachricht aus § 0: die Auswahl hängt an der Geometrie, und die ist
gemessen.

⛔ **P-3 bleibt der harte Fall.** Er entscheidet, ob je ein Beitrag für den
Hebel tragen kann — und er betrifft Spot mit.
