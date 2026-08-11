# Übergabe — Stand 11.08.2026

**Zuerst lesen, in dieser Reihenfolge:**

1. **Dieses Dokument** — Stand, nächster Schritt, offene Fäden
2. `Arbeitsstand_Deadloop_09_08.md` **Abschnitte 6 bis 7.9** — die Befunde des
   10./11.08. Abschnitt 7.9 enthält die zuletzt gefundene Ursache
3. `Rollenkonzept_Entwurf_10_08.md` — das Zielbild der LLM-Ebene, mit der
   Trennung generisch/systemabhängig bei den Bias-Effekten
4. `Regelwerk_Entscheidungslog.md` Nachträge **202 bis 204**

**Nachgezogen am 11.08., bei Detailfragen:**

| Dokument | was dort neu steht |
|---|---|
| `Regelwerksmanual.md` | **R-A1 bis R-A8** — die Regeln der Rollen-Ebene |
| `Fakten_Entscheidungsmappe.md` **Kap. 10** | der neue Faktensatz, was bewusst fehlt, der bekannte Defekt |
| `Zielgroessen_und_Erfolgsmasse.md` | **Erfolgsmaß braucht den Stop** — +22,3 % Endrendite und trotzdem ausgestoppt |
| `Test_und_Verifikationsmethodik.md` **2.18** | Prüfsteine aus der eigenen Historie, drei Zusicherungen |

Alles Weitere nur bei Bedarf. `Fakten_Entscheidungsmappe.md` Abschnitt 4.2 ist
die Bestandsaufnahme dessen, was das ALTE System dem Modell zeigt.

---

## 1. Wo wir stehen

Die LLM-Ebene wurde am 10./11.08. neu gebaut. Sie läuft, ist an echten Fällen
geprüft — und der zuletzt gefundene Defekt ist **behebbar und benannt**.

### Was gebaut und geprüft ist

| Datei | Zweck | Stand |
|---|---|---|
| `agent/empfehlung_vertrag.py` | was eine Empfehlung enthalten muss | geprüft am echten KAS-Fall |
| `agent/lagebeschreibung.py` | Asset-Lage als Aussagen, Bestand zuerst | **enthält den Defekt aus 7.9** |
| `agent/marktbreite.py` | Anteil über 50-/200-Tage-Linie | kausal geprüft |
| `agent/rolle_analyst.py` | Rolle A: Marktlage (1.114 Zeichen) | läuft |
| `agent/rolle_trader.py` | Rolle BC: Aufbau + Bestand → Handlung | läuft |
| `agent/antwort_normalisierung.py` | Formfehler korrigieren statt ablehnen | 4 harte Ablehnungsgründe |
| `agent/llm_schema.py` | Schemata aus Konstanten abgeleitet | Prompt/Schema lückenlos |
| `pruefe_rollenkette.py` | Durchlauf: trocken / ein Fall / Prüfsteine | läuft |
| `messe_betragsdeckel.py` | gepaarte Messung | Hypothese widerlegt |
| `backtest_llm1_historisch.py::lade_reihen_aus_db()` | DB statt 125-MB-JSON | neu, robuster |

**Prompt: 3.183 Zeichen gegen 34.611 im Altsystem. ~42 Aufrufe täglich statt 40.**

---

## 2. DER NÄCHSTE SCHRITT — der Defekt aus 7.9

`agent/lagebeschreibung.py::_struktur()` vergleicht die letzten **zwei**
Swing-Punkte und nennt das Ergebnis *„ein intakter Abwärtstrend"*. Bei einer
Korrektur innerhalb eines Aufwärtstrends ist das **falsch beschriftet** — und
das Modell folgt der Beschriftung, nicht der Zahl daneben.

```
Die Marktstruktur zeigt tiefere Hochs und tiefere Tiefs — ein intakter ABWÄRTSTREND.
Kursentwicklung: 5 Tage −2,9 %, 20 Tage −6,1 %, 60 Tage +37,0 %
```

Das Modell gewichtete den +37-%-Aufwärtstrend als **gering** und die zweiwöchige
Korrektur als **hoch**.

> **ÜBERHOLT am 11.08. abends — siehe `Arbeitsstand_Deadloop_09_08.md` 7.10/7.11.**
> Hier stand: *„Das erklärt sechs von sechs verpasste Gelegenheiten"* und der
> Defekt sei die Ursache des Deadloops. **Beides ist zurückgestuft:**
>
> - Die Behauptung beruht auf **einer** gelesenen Begründung, nicht auf sechs.
>   Die `betragsdeckel*.json` existiert nicht, wurde nie committet, und das
>   Skript speichert die Begründungen gar nicht (7.10).
> - Die Konstellation tritt auf **2,71 %** der Krypto-Tage auf (60T ≥ +30 %),
>   auf 6,21 % bei ≥ +10 %. Der Deadloop ist 97,5 %. **Der Defekt kann ihn
>   nicht erklären** (7.11).
> - Der **häufigere** Fehler ist das Gegenteil: „Aufwärtstrend" bei fallendem
>   60-Tage-Fenster, 11,39 %. Ein Punktfix in Richtung „mehr kaufen" verschärft
>   die größere Hälfte.
>
> Der Fix bleibt richtig — als **Textwahrheits-Defekt**, symmetrisch, und als
> Sonderfall der Regeln R-T1/R-T2. Nicht als Kur gegen den Deadloop.

**Der Fix:** Struktur relativ zur übergeordneten Bewegung formulieren, ohne
absolutes Etikett. Etwa: *„Auf Sicht von zwei Wochen tiefere Hochs und Tiefs,
innerhalb eines 60-Tage-Anstiegs von +37 % — eine Korrektur im Aufwärtstrend."*

**Danach:** Die acht Anker aus 7.8/7.9 erneut laufen lassen (16 Aufrufe) und
prüfen, ob aus den sechs NICHTS_TUN Käufe werden.

> **Diese Erfolgskontrolle allein genügt nicht.** Die acht Anker sind **nach
> ihrem Ausgang ausgewählt** — ein Fix, der `_struktur()` einfach immer
> „Aufwärtstrend" sagen ließe, bekäme darin 6 von 6. Es braucht die
> Gegenzellen (Etikett zu Recht negativ), sonst misst die Kontrolle keine
> Falsch-Positiven.

---

## 3. Der übergeordnete Plan

### Zielbild
Für jeden Aufbau eine **begründete Handlungsempfehlung**, die ein Trader lesen
und nachvollziehen kann — in Euro und Prozent, pro Asset, per E-Mail.

### Die Kette
```
Budget-Allocator wählt Assets                       (unverändert)
        ↓
ROLLE A — 1-2× am Tag        Marktlage, kein Asset, KEIN Betrag
        ↓  (Ergebnis, keine Rohdaten)
ROLLE BC — 1× je Asset       Bestand zuerst, dann Aufbau → Handlung
        ↓
Betrag deterministisch:  3+ Faktoren → 500, 2 → 300, 1 → 100, 0 → keine Handlung
        ↓
Validator: korrigieren / degradieren / warnen — nur 4 harte Ablehnungsgründe
        ↓
E-Mail je Asset + GUI                               (unverändert)
```

### Detailpläne
- **Rollenkonzept** vollständig: `Rollenkonzept_Entwurf_10_08.md`
- **Was NICHT übergeben wird** und warum: dort Abschnitt 4, jeder Block
  **einzeln zuschaltbar**, Begründungen aus dem Altsystem gelten als Hypothese
- **Bias-Effekte** mit Übertragbarkeit (generisch/systemabhängig): dort Abschnitt 2

### Offene Punkte, nach Priorität
1. **Struktur-Defekt beheben** (siehe 2) — höchste Priorität, erklärt den Deadloop
2. **Rang unter Kandidaten** — der Vergleich ist der Zuschnitt mit Evidenz
3. **Position Swapping** für beide Rollen — Muster existiert bei LLM2
4. Marktbreite: wirkt invers (7.4), Rolle A folgt ihr aktuell im Wortsinn
5. Gegenprüfer als **eigener** Aufruf (niemals im selben — Selbstvalidierung)

---

## 4. Die wichtigsten Erkenntnisse des 10./11.08.

| # | Erkenntnis | wo |
|---|---|---|
| 1 | Kein Verfahren schlägt die Basisrate — 8.441 Fälle, zwei Verfahren, zwei Merkmalsfamilien | 6.1–6.2 |
| 2 | Die Zonengeometrie verliert strukturell −0,115 R je Trade | 6.3 |
| 3 | Technische Regeln sind nach Kosten nicht profitabel (Park/Irwin, 9.000 Regeln); Krypto-Evidenz ist **querschnittlich** | 6.4 |
| 4 | Der Defekt sitzt im LLM — **Eingang und Ausgang** (Nutzerbefund, belegt am KAS-Signal) | 7.1 |
| 5 | Keine Breite-Größe sagt die 20-Tage-Rendite vorher; je breiter, desto schlechter | 7.4 |
| 6 | Der Betragsdeckel wirkt **nicht** — 13 Anker, in jedem Fall identisch | 7.7 |
| 7 | **Das System kauft fast nie** — 7 von 13 Ankern mit zweistelligen Gewinnen, 1 Handlung | 7.8 |
| 8 | **Ursache: falsch beschriftete Marktstruktur** | **7.9** |

### Stehende Vorgaben, die sich bewährt haben
- **Formfehler korrigieren, Sinnfehler ablehnen** — ein strenger Validator baut
  denselben Deadloop an anderer Stelle
- **Kein Betrag für die LLMs** — extern belegt, gilt für alle Rollen
- **Vor jedem Lauf**: Werturteil-Wächter, Konstanten-Wächter, Kausalitätsprobe
- **Erfolgsmaß mit Stop rechnen**, nicht als Endrendite — sonst zählt ein
  ausgestoppter Trade als Treffer (Fehler vom 11.08., korrigiert in 7.9)

---

## 5. Betriebliches

- **Produktion steht** seit 10.08. — bewusst, bis das neue Konzept läuft
- **Desktop-DB endet am 19.07.**, die Notebook-Exportdatei reichte bis 10.08.
- `lade_reihen()` braucht ~2 GB freien Speicher für die 125-MB-JSON; bei
  Speicherdruck `lade_reihen_aus_db()` verwenden
- Aktien stehen **nicht** im Preis-Cache — Kurse dann in Quellwährung
- Gemini-Tageskontingent: 500 je Modell, Reset 09:00 MESZ
